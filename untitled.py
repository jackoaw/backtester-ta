dependency_list = ''

class Task:

	def __init__(self, name, dependency_list):
		self.name = name
		# array of strings that it depends on
		self.dependency_list = dependency_list
		self.executed = False


	def execute(self):
		print(self.name)
		self.executed = True

depen_map = {
	'A': [],
	'B': ['A'],
	'E': ['C', 'D'],
	'C': ['B'],
	'D': ['B']
}

# Convert into a dependency map, and iterate through the map, where if you encounter a dependency not run, you go straight to that and run it
# This can be done recursively 


tasks = [ Task('A', []),
	Task('B', ['A']),
	Task('E', ['C', 'D']),
	Task('C', ['B']),
	Task('D', ['B'])
]
# Run in order based on dependency list

# Iterate through, keeping trak of whcih tasks have already run via a map or set and if dependencies are executed then execute that function 

history = {''}

total = len(tasks)

current = 0 
while current < total:
	current = 0
	for task in tasks:
		if len(task.dependency_list) > 0:
			for dependency in task.dependency_list:
				if dependency in history:
					if task.executed is False:
						task.execute()
						history.add(task.name)
					current += 1
					
				else: 
					continue
		else:
			if task.executed is False:
				task.execute()
				history.add(task.name)
			current += 1


	