import networkx as nx
import nxmetis
import os
import random

###########################################
# Change this variable to the path to 
# the folder containing all three input
# size category folders
###########################################
path_to_inputs = "all_inputs"

###########################################
# Change this variable if you want
# your outputs to be put in a 
# different folder
###########################################
path_to_outputs = "outputs"

def parse_input(folder_name):
    '''
        Parses an input and returns the corresponding graph and parameters

        Inputs:
            folder_name - a string representing the path to the input folder

        Outputs:
            (graph, num_buses, size_bus, constraints)
            graph - the graph as a NetworkX object
            num_buses - an integer representing the number of buses you can allocate to
            size_buses - an integer representing the number of students that can fit on a bus
            constraints - a list where each element is a list vertices which represents a single rowdy group
    '''
    graph = nx.read_gml(folder_name + "/graph.gml")
    parameters = open(folder_name + "/parameters.txt")
    num_buses = int(parameters.readline())
    size_bus = int(parameters.readline())
    constraints = []
    
    for line in parameters:
        line = line[1: -2]
        curr_constraint = [num.replace("'", "") for num in line.split(", ")]
        constraints.append(curr_constraint)

    return graph, num_buses, size_bus, constraints

#checks if l1 is a sublist of l2
def sublist(l1, l2):
    return all([item in l2 for item in l1])

def scoreIt(graph, assignments, num_buses, size_bus, constraints):
    if len(assignments) != num_buses:
        return -1
    
    # make sure no bus is empty or above capacity
    for i in range(len(assignments)):
        if len(assignments[i]) > size_bus:
            return -1
        if len(assignments[i]) <= 0:
            return -1
        
    bus_assignments = {}
    attendance_count = 0
        
    # make sure each student is in exactly one bus
    attendance = {student: False for student in graph.nodes()}
    for i in range(len(assignments)):
        if not all([student in graph for student in assignments[i]]):
            return -1

        for student in assignments[i]:
            # if a student appears more than once
            if attendance[student] == True:
                print(assignments[i])
                return -1
                
            attendance[student] = True
            bus_assignments[student] = i
    
    # make sure each student is accounted for
    if not all(attendance.values()):
        return -1
    
    total_edges = graph.number_of_edges()
    # Remove nodes for rowdy groups which were not broken up
    for i in range(len(constraints)):
        busses = set()
        for student in constraints[i]:
            busses.add(bus_assignments[student])
        if len(busses) <= 1:
            for student in constraints[i]:
                if student in graph:
                    graph.remove_node(student)
    # score output
    score = 0
    for edge in graph.edges():
        if bus_assignments[edge[0]] == bus_assignments[edge[1]]:
            score += 1
    score = score / total_edges
    return score


def generateMETIS(G, path):
    f = open(path + '/metis.in', 'w')
    f2 = open(path + '/mappings.txt', 'w')
    f.write(str(G.number_of_nodes()) + ' ' + str(G.number_of_edges()) + '\n')
    lookup = {}
    i = 1
    for node in G.nodes():
        lookup[node] = i
        i += 1
    line = ''
    for node in G.nodes():
        line = ' '.join([str(lookup[adjNode]) for adjNode in G[node]])
        f.write(line + '\n')
        f2.write(str(lookup[node]) + ' ' + node + '\n')
    f.close()
    f2.close()

def solve(G, k, s, rowdy_groups, i):
    #TODO: Write this method as you like. We'd recommend changing the arguments here as well
    #precalculate rowdy groups
    #K = number of buses.
    #S = max bus size.

    #29's messed up
    if i == 29 or i == 1064:
        nodes = list(G.nodes())
        step = len(nodes)//k
        return [nodes[j:j+step] for j in range(0, len(nodes), step)]

    seedr = random.randint(0,100000)
    buses=[]
    options = nxmetis.MetisOptions(seed = seedr)
    vol, buses = nxmetis.partition(G, k, recursive=True, options=options)
    #adjust for < S
    if any([1 for bus in buses if len(bus) > s]):
        #readjust partition.
        print(s, k, [len(bus) for bus in buses])
        #O(N) algorithm to by-hand pick off and rebalance
        picks = []
        for j in range(len(buses)):
            if len(buses[j]) > s:
                picks.extend(buses[j][s:])
                buses[j] = buses[j][:s]
        for j in range(len(buses)):
            if len(buses[j]) < s:
                space = s - len(buses[j])
                buses[j].extend(picks[len(picks)-space:])
                picks=picks[:len(picks)-space]
        print(s, k, [len(bus) for bus in buses])
    return buses

def solveSet(G, k, s, rowdy_groups, i):
    bestScore = 0
    bestBuses = []
    for r in range(5):
        buses = solve(G, k, s, rowdy_groups, i)
        score = scoreIt(G, buses, k, s, rowdy_groups)
        if score > bestScore:
            bestBuses = buses
            bestScore = score
            print(score)
    return bestBuses

def main(): 
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ['large'] #CHANGE THIS
    for size in size_categories:
        for i in range(1064, 1100):
            if i%5==0: #every 5: print status.
                print(i)               
            in_path = path_to_inputs + "/" + size + "/" + str(i)
            out_path = path_to_outputs + "/" + size + "/"

            if not os.path.exists(in_path):
                continue
            if not os.path.exists(out_path):
                os.makedirs(out_path)

            #parse
            graph, num_buses, size_bus, constraints = parse_input(in_path)
            #solve
            
            solution_buses = solve(graph, num_buses, size_bus, constraints, i)

            output_file = open(out_path + str(i) + ".out", "w")

            #TODO: modify this to write your solution to your 
            #      file properly as it might not be correct to 
            #      just write the variable solution to a file
            for students_in_bus in solution_buses:
                output_file.write(str(students_in_bus) + '\n')
            output_file.close()

if __name__ == '__main__':
    main()


