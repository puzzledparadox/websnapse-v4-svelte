import numpy as np
from engine import get_all_next_nondet, compute_stv_k

def build_configuration_graph(initial_state, raw_nodes, adjacency, rules_metadata, m_pi, rule_delays, max_states=500):
	"""
	Builds the configuration graph using BFS to explore the state space of an SN P system.
	Labels match the theoretical notation in Fig. 2 (neuron and rule indices, s for delay, 0 for idle).
	Sorts neurons by numeric ID to ensure consistent vector ordering in labels.
	"""
	
	has_inputs = any(n.get('neuronType', 'regular') in ('input', 'Input') for n in raw_nodes)
	
	# Determine sorting order for neurons based on numeric ID (e.g. n1, n2, n3)
	def get_numeric_id(node):
		# Prioritize userLabel for sorting to match user's mental model
		nid = node.get('userLabel', node.get('id', ''))
		numeric = ''.join(filter(str.isdigit, str(nid)))
		return int(numeric) if numeric else str(nid)

	indexed_nodes = list(enumerate(raw_nodes))
	sorted_indices = [i for i, n in sorted(indexed_nodes, key=lambda x: get_numeric_id(x[1]))]
	original_to_sorted = {orig: rank for rank, orig in enumerate(sorted_indices)}
	
	clean_ids = []
	for n in raw_nodes:
		# Use userLabel (original data.id) for display, falling back to topological id
		nid = n.get('userLabel', n.get('id', ''))
		numeric = ''.join(filter(str.isdigit, str(nid)))
		clean_ids.append(numeric if numeric else str(nid))

	def get_state_sig(state, tick):
		if has_inputs:
			return (tuple(state['c_k']), tuple(state['div']), tuple(state['dsv']), tick)
		else:
			return (tuple(state['c_k']), tuple(state['div']), tuple(state['dsv']))
	
	def get_node_label(state):
		c_k = state['c_k']
		div = state['div']
		dsv = state['dsv']
		
		parts = ["" for _ in range(len(raw_nodes))]
		rule_idx = 0
		for neuron_idx, node in enumerate(raw_nodes):
			rule_count = len(node.get('rules', []))
			delay_val = 0
			for r in range(rule_count):
				global_r = rule_idx + r
				if global_r < len(div) and div[global_r] == 1 and dsv[global_r] > 0:
					delay_val = dsv[global_r]
					break
			rule_idx += rule_count
			
			sorted_rank = original_to_sorted[neuron_idx]
			parts[sorted_rank] = f"{c_k[neuron_idx]}/{delay_val}"
				
		return "⟨" + ", ".join(parts) + "⟩"

	def get_rule_labels(dv, div, dsv):
		"""
		Returns the rule firing set in the style of Fig 2:
		- i{rule_index} if rule fired
		- is if neuron is in delay (closed)
		- i0 if no rule fired
		"""
		labels = []
		rule_idx = 0
		
		# We want to iterate in sorted neuron order for the label
		# But dv/div/dsv are in original order.
		neuron_labels = ["" for _ in range(len(raw_nodes))]
		
		for neuron_idx, node in enumerate(raw_nodes):
			n_id = clean_ids[neuron_idx]
			rule_count = len(node.get('rules', []))
			
			# 1. Check if neuron is in delay
			is_closed = False
			for r in range(rule_count):
				global_r = rule_idx + r
				if global_r < len(div) and div[global_r] == 1 and dsv[global_r] > 0:
					is_closed = True
					break
			
			label = ""
			if is_closed:
				label = f"{n_id}s"
			else:
				# 2. Check if a rule fired
				fired_rule_idx = -1
				for r in range(rule_count):
					global_r = rule_idx + r
					if global_r < len(dv) and dv[global_r] == 1:
						fired_rule_idx = r + 1
						break
				
				if fired_rule_idx != -1:
					label = f"{n_id}{fired_rule_idx}"
				else:
					# 3. Idle
					label = f"{n_id}0"
			
			sorted_rank = original_to_sorted[neuron_idx]
			neuron_labels[sorted_rank] = label
			rule_idx += rule_count
			
		return ", ".join(neuron_labels)

	start_sig = get_state_sig(initial_state, 0)
	
	nodes = []
	edges = []
	visited = {}
	visited[start_sig] = "n0"
	
	nodes.append({
		"id": "n0",
		"label": get_node_label(initial_state),
		"is_halted": False 
	})
	
	queue = [(initial_state, "n0", 0)] 
	state_count = 1
	edge_count = 0
	
	while queue and state_count <= max_states:
		curr_state, curr_id, tick = queue.pop(0)
		
		shifted_nodes = []
		for node in raw_nodes:
			new_node = node.copy()
			if node.get('neuronType', 'regular') in ('input', 'Input'):
				train = str(node.get('spikes', ''))
				new_node['spikes'] = train[tick:] if tick < len(train) else ""
			shifted_nodes.append(new_node)
		
		stv_k, inputs_active = compute_stv_k(0, shifted_nodes, adjacency)
		next_possibilities = get_all_next_nondet(curr_state, rules_metadata, m_pi, stv_k, rule_delays, adjacency, inputs_active)
		
		# Halting check: a state is halted ONLY if no rules can be applied
		# and no rules are currently firing.
		is_halted = False
		if not next_possibilities and not inputs_active:
			is_halted = True
		elif next_possibilities and not inputs_active:
			# Check if ALL possibilities are "idling" (no rules fired, no rules selected)
			all_idling = True
			for nxt in next_possibilities:
				# nxt['dv'] are rules selected this tick
				# nxt['iv'] are rules firing (producing spikes) this tick
				if np.any(nxt['dv'] > 0) or np.any(nxt['iv'] > 0):
					all_idling = False
					break
			if all_idling:
				is_halted = True
		
		if is_halted:
			for n in nodes:
				if n['id'] == curr_id:
					n['is_halted'] = True
					break
			continue  # No outgoing edges from halted states
			
		for nxt in next_possibilities:
			sig = get_state_sig(nxt, tick + 1)
			
			if sig not in visited:
				if state_count >= max_states:
					continue
					
				new_id = f"n{state_count}"
				visited[sig] = new_id
				state_count += 1
				
				nodes.append({
					"id": new_id,
					"label": get_node_label(nxt),
					"is_halted": False
				})
				
				queue.append((nxt, new_id, tick + 1))
			
			target_id = visited[sig]
			# Pass current state's div/dsv to determine 's' (closed) status for the transition
			rules_label = get_rule_labels(nxt['dv'], curr_state['div'], curr_state['dsv'])
			
			edges.append({
				"id": f"e{edge_count}",
				"source": curr_id,
				"target": target_id,
				"label": rules_label
			})
			edge_count += 1

	return {
		"nodes": nodes,
		"edges": edges,
		"limit_reached": state_count >= max_states
	}
