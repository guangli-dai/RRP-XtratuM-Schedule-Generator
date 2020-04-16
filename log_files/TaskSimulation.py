import sys
import random

class time_spot:
	def __init__(self, time, counter):
		self.time = time
		self.counter = counter

class task:
	def __init__(self, arrival, wcet, deadline):
		self.arrival_time = arrival
		self.wcet = wcet
		self.deadline = deadline


def file_analysis(filename):
	'''
	This function analyzes the file with filename and stores the result to lists of time_spot objects.
	'''
	print("reading")
	p1_list = []
	p2_list = []
	with open(filename, 'r') as f:
		lines = f.readlines()
		for line in lines:
			line = line[:-2]
			#print(line)
			elements = line.split(',')
			time_now = int(elements[4])
			p1_counter = int(elements[1])
			p2_counter = int(elements[2])
			spot1 = time_spot(time_now, p1_counter)
			p1_list.append(spot1)
			spot2 = time_spot(time_now, p2_counter)
			p2_list.append(spot2)
	return (p1_list, p2_list)

def search_time(time, p_list):
	'''
	This function returns the index of the smallest item in p_list with time larger than time.
	if none can be found, return -1
	'''
	start = 0
	end = len(p_list) - 1
	result = -1
	while start < end:
		middle = int((start + end)/2)
		#print(str(start)+','+str(middle)+','+str(end))
		#print(p_list[middle].time)
		if p_list[middle].time == time:
			return middle
		elif p_list[middle].time < time:
			start = middle + 1
		else:
			result = middle
			end = middle - 1
	return result

def search_counter(counter, p_list):
	'''
	This function returns the index of the smallest item in p_list with counter larger than counter.
	if none can be found, return -1
	'''
	start = 0
	end = len(p_list) - 1
	result = -1
	while start < end:
		middle = int((start + end)/2)
		#print(str(start)+','+str(middle)+','+str(end))
		if p_list[middle].counter == counter:
			return middle
		elif p_list[middle].counter < counter:
			start = middle + 1
		else:
			result = middle
			end = middle - 1
	return result

def execute_task(task_now, p_list):
	'''
	This function judges whether the task can be accomplished in time with info in p_list.
	'''
	#search the place of arrival
	#print("Searching.")
	index_start = search_time(task_now.arrival_time, p_list)
	if index_start == -1 or index_start == 0:
		print("Error! The task arrival time is out of bound.")
		return False

	start_counter = p_list[index_start].counter - (p_list[index_start].time - task_now.arrival_time)/(p_list[index_start].time - p_list[index_start-1].time)*(p_list[index_start].counter - p_list[index_start-1].counter)
	start_counter = int(start_counter)
	print('Start counter is:'+str(start_counter))
	end_counter = start_counter + task_now.wcet
	index_end = search_counter(end_counter, p_list)
	if index_end == -1:
		print("Error! Unable to accomplish the task with the given log.")
		return False
	while index_end>0 and p_list[index_end].counter == p_list[index_end-1].counter:
		index_end -= 1
	end_time = p_list[index_end].time - (p_list[index_end].counter - end_counter)/(p_list[index_end].counter - p_list[index_end-1].counter)*(p_list[index_end].time - p_list[index_end-1].time)
	print(end_time)
	if end_time > task_now.deadline:
		return False
	return True

def generate_task(density):
	inc_per_us = 2.4239
	arrival_time = random.randint(150000, 300000)
	wcet = random.randint(10000, 100000)
	ddl = (wcet/inc_per_us)/density + arrival_time
	print(arrival_time)
	print(wcet)
	print(ddl)
	task_now = task(arrival_time, wcet,ddl)
	return task_now


if len(sys.argv) >1:
	
(p1_list, p2_list) = file_analysis('3_7_4_7_RRP_10ms.log')
#print(p1_list)
for i in range(1000):

task_now = generate_task(0.45)
print(execute_task(task_now, p1_list))