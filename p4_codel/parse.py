import json


def evaluateIperf3(raw_data):

    stats = []
    avg_throughput, avg_y, max_rtt, min_rtt, max_tput, min_tput = 0, 0, 0, 0, 0, 0

    y_values = []
    for data in raw_data:
        y_val = 0
        for x in data:
            y_val += x['rtt']/1000.0
        y_val = y_val/len(data)
        # Get min and max RTT
        if y_val < min_rtt:
            min_rtt = y_val
        if y_val > max_rtt:
            max_rtt = y_val
            # initially set min_rtt value as well
            if min_rtt == 0:
                min_rtt = max_rtt
        avg_y += y_val
        y_values.append(y_val)
    avg_y = avg_y / len(y_values)
    
    stats.append(avg_y/2)
    stats.append(max_rtt/2)
    stats.append(min_rtt/2)
    
    #print("Average lat.: %d" %(avg_y/2))
    #print("Max lat.: %d" %(max_rtt/2))
    #print("Min lat.: %d" %(min_rtt/2))
   
    y_values = []
    for data in raw_data:
        y_val = 0
        for x in data:
            y_val += x['bytes'] / x['seconds']
        y_val = y_val/1000
        # Get min and max Throughput
        if y_val < min_tput:
            min_tput = y_val
        if y_val > max_tput:
            max_tput = y_val
            if min_tput == 0:
                min_tput = max_tput
        y_values.append(y_val)
        avg_throughput += y_val
    avg_throughput = avg_throughput / len(y_values)

    stats.append(avg_throughput)
    stats.append(max_tput)
    stats.append(min_tput)
    
    #print("Average Throughput: %d" %(avg_throughput))
    #print("Max Throughput: %d" %(max_tput))
    #print("Min Throughput: %d" %(min_tput))

    return stats

def getStats(filename):
    file = open('../out/' + filename + '.json', "r")
    content = file.read()
    content = json.loads(content)
    #now content is a dict
    loRawInputs = content['intervals']
    resLst = []
    for x in loRawInputs:
        innerLst = []
        for y in x['streams']:
            innerLst.append(y) #TODO hier wird nur der erste Stream geparst
        resLst.append(innerLst)

    statistics = evaluateIperf3(resLst)

    return statistics

if __name__ == "__main__":
    
    iter = 10
    Net_BW = 53
    latencies = ["5", "10", "15", "20", "30", "40", "50", "60", "70"]
    min_latency = "5"
    
    for l in range(latencies.index(min_latency),len(latencies)):
        filename = min_latency + latencies[l]

        fair, util, max_latency, avg_latency = 0, 0, 0, 0

        for i in range(iter):

            # json files of the two flows for the configs
            filename1 = filename + str(i) + "/test1" 
            filename2 = filename + str(i) + "/test2"

            stats1 = getStats(filename1)
            stats2 = getStats(filename2)

            # Throughput is in KBps
            fair += pow((stats1[3] + stats2[3]), 2) / (2 * (pow(stats1[3], 2) + pow(stats2[3], 2)))
            #util += (stats1[3] + stats2[3]) / Net_BW
	    '''	
            if (stats1[1] > max_latency):
                max_latency = stats1[1]
            
            avg_latency += stats1[0]
	    '''
        fair /= iter
        util /= iter
        avg_latency /= iter
        
        print (fair)
        #print ("-------------------------------------------------------------------------")

