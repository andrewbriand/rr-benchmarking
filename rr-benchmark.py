import roadrunner
import time

file_name = argv[1]

rr = roadrunner.RoadRunner(file_name + ".xml")

rr.getIntegrator().setValue("absolute_tolerance", 1e-9)
rr.getIntegrator().setValue("relative_tolerance", 1e-12)

times = []
result = []

for i in range(100):
    start = time.time()
    rr.reset()
    result = rr.simulate(0, 50, 100)
    end = time.time()
    times.append(end - start)

time_file = open("rr-benchmark-times-" + file_name + ".txt", "w")
for t in times:
    time_file.write("%.14f\n" % t)

results_file = open("rr-benchmark-results-" + file_name + ".txt", "w")
for i in range(1, len(result[0])):
    for r in result:
        results_file.write("%.14f\n" % r[i])
