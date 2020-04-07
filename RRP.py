'''
author: Guangli Dai @RTLab @UH
'''
import math
import copy
import xml.etree.ElementTree as ET
class Partition:
    def __init__(self, wcet, period, partition_id):
        '''
        Args:
            wcet:            type: int; Worst case execution time in each period of the partition.
            period:            type: int; The length of a period of the partition. availability factor is WCET/period.
            aaf:            type: double; Approximate availability factor.
            partition_id:           type: int; The id of the partition.
        '''
        self.wcet = wcet
        self.period = period
        self.aaf = float(wcet)/period #the approximate availability factor is set as availability factor initially.
        self.partition_id = partition_id


class sched_entry:
        def __init__(self, start_time, end_time, partition_id):
                '''
                Args:
                        start_time:             type: int; Start time of the sched entry, given in milliseconds.
                        end_time:               type: int; End time of the sched entry, given in milliseconds.
                        partition_id:           type: int; The id of the partition in the sched entry.
                '''
                self.start_time = start_time
                self.end_time = end_time
                self.partition_id = partition_id


class RRP:
    def set_partitions(self, par_list, CPU_num, time_slice_len=100, xml_file_name='xm_cf.arm.xml', processor_freq=400):
                '''
                Args:
                        par_list:               type: list; A list of partitions to be scheduled.
                        CPU_num:                type: int; The number of CPU to be scheduled on.
                        time_slice_len:         type: int; The length of each time slice, given in milliseconds.
                        xml_file_name:          type: string; The name of the xml file
                        processor_freq:         type: int; The frequency of processors, given in MHz.
                Returns:
                        returns a boolean value to indicate whether the partitions are schedulable or now. True for schedulable, False for non-schedulable.
                '''
                if CPU_num>1:
                    #execute mulZ here
                    print("Executing mulZ.\n")
                    launch_tables = self.MulZ(par_list, CPU_num)
                    if launch_tables is None:
                        return False
                    CPU_counter = 0
                    (tree, processor_table) = self.parse_xml(xml_file_name)
                    if tree is None or processor_table is None:
                        return False
                    #wipe the processors out first
                    for processor in processor_table.findall('{http://www.xtratum.org/xm-arm-2.x}Processor'):
                        processor_table.remove(processor)
                    for lt in launch_tables:
                            #update the processor information
                            print("Launch table for CPU "+str(CPU_counter)+" :")
                            processor_now = ET.SubElement(processor_table, 'Processor')
                            processor_now.set('id', str(CPU_counter))
                            processor_now.set('frequency',str(processor_freq)+'Mhz')
                            self.output_launch_table(processor_now, lt, time_slice_len)
                            self.print_launch_table(lt)
                            CPU_counter += 1
                    tree.write(xml_file_name)
                else:
                    #execute Magic7 here
                    print("Executing Magic7.\n")
                    for par in par_list:
                            self.magic7(par)
                    launch_table = self.partition_single(par_list)
                    if launch_table is None:
                        print("Unschedulable!")
                        return False
                    print("Launch table generated is:")
                    self.print_launch_table(launch_table)
                    #retrieve the node in the xml file
                    (tree, processor_table) = self.parse_xml(xml_file_name)
                    if tree is None or processor_table is None:
                        return False 
                    #wipe the processors out first
                    for processor in processor_table.findall('{http://www.xtratum.org/xm-arm-2.x}Processor'):
                        #print(processor.tag)
                        processor_table.remove(processor)
                    #write the Processor in 
                    processor = ET.SubElement(processor_table, 'Processor')
                    processor.set('frequency',str(processor_freq)+'Mhz')
                    processor.set('id','0')
                    self.output_launch_table(processor, launch_table, time_slice_len)
                    tree.write(xml_file_name)
                return True

    def cal_hyperperiod(self, par_list):
                '''
                Args:
                        par_list:               type: list; A list of partitions to be scheduled.
                Returns:
                        hyperperiod:            type: int; The hyperperiod of the partitions to be scheduled.
                '''
                hyperperiod = 0
                for par in par_list:
                    if hyperperiod==0:
                        hyperperiod = par.period
                    else:
                        hyperperiod = self.lcm(hyperperiod, par.period)
                return hyperperiod

    def lcm(self, a, b):
                '''
                This function calculates the least common multiple of a and b.
                '''
                mul = a*b
                larger = max(a,b)
                smaller = min(a,b)
                while smaller!=0:
                    t = larger%smaller
                    larger = smaller
                    smaller = t
                mul /= larger
                return mul

    def check_delta(self, avail_set, standard_p, delta, p):
                '''
                This function checks whether right-shifted by delta, standard_p is compatible with avail
                p is the period of the current partition.
                '''
                for t_now in standard_p:
                    t_del = (t_now + delta)%p
                    if t_del not in avail_set:
                        return False
                return True

    def find_delta(self, avail_set, p, q, q_left):
                '''
                Args:
                        avail:                  type: set; The set of available time slices.
                        p:                      type: Integer; The period of the target partition.
                        q:                      type: Integer; The WCET of the target partition.
                Returns:
                        delta1: The shifted value for the target partition
                '''
                standard_p1 = []
                for k in range(q):
                    t_now = int(math.floor(k*p/q))%p
                    standard_p1.append(t_now)
                standard_p2 = []
                for k in range(q_left):
                    t_now = int(math.floor(k*p/(p-q)))%p
                    standard_p2.append(t_now)
                #find potential delta1 first (delta<p)
                for delta1 in range(p):
                    if self.check_delta(avail_set, standard_p1, delta1, p):
                        #check delta2, if it is compatible, then return this delta1
                        partition1_set = set()
                        for t in standard_p1:
                            partition1_set.add((t+delta1)%p)
                        new_avail_set = avail_set - partition1_set
                        for delta2 in range(p):
                            if self.check_delta(new_avail_set, standard_p2, delta2, p):
                                return delta1
                        #otherwise, keep checking different delta1
                return -1




    def partition_single(self, partition_list):
                '''
                Args:
                        partition_list:         type: list; A list of partitions to be scheduled on this core.
                Returns:
                        launch_table            type: list; A list of parition ids that represents the final schedule. If the id is -1, that means the time slice is idle.
                '''
                #calculate the hyperperiod first and sort the partition_list based on aaf
                hyperperiod = int(self.cal_hyperperiod(partition_list))
                partition_list.sort(key=lambda x:x.aaf,reverse=True)
                #Initialize parameters needed.
                avail_timeslices = set()
                for i in range(hyperperiod):
                    avail_timeslices.add(i)
                launch_table = [-1 for x in range(hyperperiod)]
                #start allocating time slices
                i = 0
                for par in partition_list:
                    occupied_time_index = set()
                    if par.wcet!=1:
                        delta1 = self.find_delta(avail_timeslices, par.period, par.wcet, int(len(avail_timeslices)/hyperperiod*par.period) - par.wcet)
                        if delta1 == -1:
                            print("Unschedulable partitions!")
                            return None 
                        for l in range(int(hyperperiod/par.period)):
                            for k in range(par.wcet):
                                index_now = int(math.floor(k*par.period/par.wcet)+delta1)%par.period + l*par.period
                                if index_now not in avail_timeslices:
                                    print("Something wrong with time slice"+str(index_now))
                                    return None
                                launch_table[index_now] = par.partition_id
                                occupied_time_index.add(index_now)
                    else:
                        index = min(avail_timeslices)
                        if index>= par.period:
                            print("Unschedulable partitions!")
                            return None 
                        for l in range(int(hyperperiod/par.period)):
                            index_now = index + l * par.period
                            launch_table[index_now] = par.partition_id
                            occupied_time_index.add(index_now)
                    #update the overall information
                    avail_timeslices = avail_timeslices - occupied_time_index
                #return the launch table, which is the schedule
                return launch_table

    def approximate_value(self, value):
                '''
                This function approximates the value given to the multiple of 0.5 when they are closed enough.
                '''
                result = math.floor(value)
                if value - result> 0.99999:
                        return result + 1
                elif value - result > 0.49999 and value - result < 0.5:
                        return result + 0.5
                elif value - result > 0 and value - result < 0.00001:
                        return result
                return value

    def magic7(self, par):
                '''
                This function takes in a partition and calculates its approximate availability factor. Accordingly, the wcet and period of the partition will be updated as well.
                Only regular partitions are considered in this version, i.e., regularity is always 1.
                The initial availability_factor should not be larger than 1. If it is larger than 1, the return value will be 1 as well.
                '''
                #initiate availability_factor with is wcet/period.
                availability_factor = float(par.wcet)/par.period
                if availability_factor == 0:
                        par.aaf = 0
                        par.wcet = 0
                        par.period = 1
                        return
                elif availability_factor > 0 and availability_factor < 1.0/7:
                        n = math.floor(self.approximate_value(math.log(7*availability_factor)/math.log(0.5)))
                        par.aaf = 1/(7*(2**n))
                        par.wcet = 1
                        par.period = (7*(2**n))
                        return
                elif availability_factor >= 1.0/7 and availability_factor <= 6.0/7:
                        par.aaf = (math.ceil(self.approximate_value(7*availability_factor)))/7.0
                        par.wcet = math.ceil(self.approximate_value(7*availability_factor))
                        par.period = 7
                        return
                elif availability_factor > 6.0/7 and availability_factor < 1:
                        n = math.ceil(self.approximate_value(math.log(7*(1-availability_factor))/math.log(0.5)))
                        par.aaf = 1-(1/(7*(2**n)))
                        par.period = 7*(2**n)
                        par.wcet = 7*(2**n) - 1
                        return
                else:
                        par.aaf = 1
                        par.period = 1
                        par.wcet = 1
                        return
    def MulZ(self, partition_list, CPU_num):
                '''
                Args:
                        partition_list:                     type: list. A list of partitions to be scheduled.
                        CPU_num:                    type: int. The number of CPUs available to schedule on.
                Returns:
                        launch_tables:              type: A 2D array, each array is the launch table of the corresponding CPU. Inside the launch table, each element is the partition id for the time slice. Returns None when the partitions are not schedulable.
                '''
                #initialize the dict to store partitions allocated to each pcpu
                pcpu_partitions_dict = []
                pcpu_factors = []
                pcpu_rests = []        
                for i in range(int(CPU_num)):
                        pcpu_partitions_dict.append([])
                        pcpu_factors.append(0)
                        pcpu_rests.append(1)
                #sort partition list based on aaf in reversed way
                partition_list.sort(key=lambda x: x.aaf, reverse = True)
                for par in partition_list:
                        f = self.MulZ_alloc(par, pcpu_factors, pcpu_rests)
                        if f is None:
                                #if the partition is not schedulable, return None
                                return None
                        pcpu_partitions_dict[f].append(par)
                #aaf of each partition is already set during mulZ_FFD_Alloc so simply do partition_single for each pcpu.
                launch_tables = []
                for i in range(int(CPU_num)):
                        temp = self.partition_single(pcpu_partitions_dict[i])
                        if temp is None:
                            print("Something wrong with MulZ!")
                            return None
                        launch_tables.append(temp)
                return launch_tables

    def z_approx(self, w, n):
                '''
                This function returns the corresponding approximate availability factor under base Z n,2.
                '''
                i = 1
                j = 0
                m = 2
                largest = 1
                result = (1,1,1)
                while True:
                        if (n-i)/n >= w and (n-i != 1):
                                largest = (n-i)/n
                                result = (largest, n-i, n)
                                i += 1
                        else:
                                denom = n*m**j
                                if 1/denom >=w:
                                        largest = 1/denom
                                        result = (largest, 1, denom)
                                        j += 1
                                else:
                                        return result
                return -1
    def MulZ_alloc(self, par, pcpu_factors, pcpu_rests):
                '''
                Args:
                        par:                    type: Partition. The partition to be assigned to a CPU. 
                        pcpu_factors:           type: list. A list of factors of pcpus, updated by MulZ_alloc.
                        pcpu_rests:             type: list. A list of decimals indicating the space left on each pcpu, updated by MulZ_alloc.
                Returns:
                        pcpu_id: int. Returns the pcpu_id of the cpu partition par is assigned to. Note that the aaf of partition par will be modified accordingly in this function as well. 
                '''
                fixed_list = [3,4,5,7]
                smallest = 2 #smallest records the final aaf, which should be no larger than 1. 
                smallest_up = 1
                smallest_down = 1
                f = -1 #f is used to record the base chosen, candidates are [3,4,5,7]
                for x in range(4):
                        num = self.z_approx(par.aaf, fixed_list[x])
                        if num[0] < smallest:
                                f = fixed_list[x]
                                smallest = num[0]
                                smallest_up = num[1]
                                smallest_down = num[2]
                r = smallest
                for i in range(len(pcpu_factors)):
                        #if a cpu is empty, put the partition there
                        if pcpu_factors[i] == 0:
                                pcpu_factors[i] = f
                                pcpu_rests[i] = 1 - r
                                par.aaf = r
                                par.wcet = smallest_up
                                par.period = smallest_down
                                return i
                        #if a non-empty pcpu can fit it under its factor, put it in.
                        else:
                                temp = self.z_approx(par.aaf, pcpu_factors[i])
                                if pcpu_rests[i] >= temp[0]:
                                    r = temp[0]
                                    pcpu_rests[i] -= r
                                    par.aaf = r
                                    par.wcet = temp[1]
                                    par.period = temp[2]
                                    return i
                return None

    def print_launch_table(self, launch_table):
                '''
                This function prints the launch table out.
                '''                       
                counter = 0         
                for entry in launch_table:
                        print("Time slice "+str(counter)+" : "+str(entry))
                        counter += 1
    
    def output_launch_table(self, processor_node, launch_table, time_slice_len):
                '''
                Args:
                        processor_node:            type: Element in xml.etree.ElementTree; This is the node where the launch table should be inserted.
                        launch_table:               type: List; Stores the id of the partition in the corresponding time slice.
                        time_slice_len:             type: int; Indicates the length of each time slice
                Returns:
                        This function does not return anything. All modifications are done in the processor_node.
                        It is assumed that launch_table is not empty.
                '''
                plan_table_node = ET.SubElement(processor_node, 'CyclicPlanTable')
                plan_node = ET.SubElement(plan_table_node, 'Plan')
                plan_node.set('id', '0')
                plan_node.set('majorFrame', str(len(launch_table)*time_slice_len)+'ms')
                last_id = launch_table[0]
                time_now = 0
                counter = 0
                duration = 0
                for entry in launch_table:
                    if entry == last_id:
                        duration += time_slice_len
                        continue
                    if last_id!=-1:
                        slot = ET.SubElement(plan_node, 'Slot')
                        slot.set('id', str(counter))
                        slot.set('start', str(time_now)+'ms')
                        slot.set('duration', str(duration)+'ms')
                        slot.set('partitionId',str(last_id))
                        counter += 1
                    #reset after setting one entry
                    time_now += duration
                    duration = time_slice_len
                    last_id = entry
                #write the last entry in
                if last_id!=-1:
                    slot = ET.SubElement(plan_node, 'Slot')
                    slot.set('id', str(counter))
                    slot.set('start', str(time_now)+'ms')
                    slot.set('duration', str(duration)+'ms')
                    slot.set('partitionId',str(last_id))

    def parse_xml(self, xml_file_name):
                '''
                Args:
                        xml_file_name:               type:string; The name of the target xml file.
                Returns:
                        A tuple. The first element is the tree handle of the whole xml file. The second element that contains the node of ProcessorTable.
                        If the file passed in does not fit the format, a None will be returned.
                '''
                try:
                    ET.register_namespace('', 'http://www.xtratum.org/xm-arm-2.x')
                    tree = ET.ElementTree()
                    tree.parse(xml_file_name)
                    root = tree.getroot()
                    hw_description= root[0]
                    processor_table = None
                    for node in hw_description:
                        #print(node.tag)
                        if node.tag.find('ProcessorTable')!=-1:
                            processor_table = node
                            break
                    if processor_table is None:
                        processor_table = ET.SubElement(hw_description, 'ProcessorTable')
                    return (tree, processor_table)
                except (ET.ParseError, IndexError):
                    print('The given xml file is not properly formatted.')
                    return (None,None)

    def get_partition_info(self):
                '''
                Entry of the class. 
                This function helps retrieve partitions' information from the input.
                Target file and the frequency of processors are required to be inserted as well.
                '''
                par_num = input("Please input the number of partitions: ")
                ps = []
                for i in range(int(par_num)):
                    id_now = input("Please input the id of partition "+str(i+1)+":")
                    wcet_now = input("Please input the WCET of partition "+str(i+1)+":")
                    period_now = input("Please input the period of partition "+str(i+1)+":")
                    par_now = Partition(float(wcet_now), float(period_now), int(id_now))
                    ps.append(par_now)
                CPU_num = int(input("Please input the number of processors:"))
                xml_file_name = input("Please input the file name of xml (default value is \'./xm_cf.arm.xml\''):")
                if xml_file_name == '':
                    xml_file_name = 'xm_cf.arm.xml'
                processor_freq = input("Please input the frequency of processors (default value is 400Mhz):")
                if processor_freq == '':
                    processor_freq = 400
                processor_freq = int(processor_freq)
                time_slice_len = input("Please input the length of each time slice (default value is 100ms):")
                if time_slice_len == '':
                    time_slice_len = 100
                time_slice_len = int(time_slice_len)
                self.set_partitions(ps, CPU_num, time_slice_len, xml_file_name, processor_freq)


#main function
if __name__=="__main__":
    rrp = RRP()
    rrp.get_partition_info()
