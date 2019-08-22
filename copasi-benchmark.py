from COPASI import *

import time

file_name = argv[1]

datamodel = CRootContainer.addDatamodel()

sbml_file = open(file_name + ".xml", "r")
assert(datamodel.importSBMLFromString(sbml_file.read()))

model = datamodel.getModel()

assert model is not None 

# get the trajectory task object
trajectoryTask = datamodel.getTask("Time-Course")
assert (isinstance(trajectoryTask, CTrajectoryTask))

# run a deterministic time course
trajectoryTask.setMethodType(CTaskEnum.Method_deterministic)

# activate the task so that it will be run when the model is saved
# and passed to CopasiSE
trajectoryTask.setScheduled(True)

# create a new report that captures the time course result
#report = create_report(model)
### set the report for the task
#trajectoryTask.getReport().setReportDefinition(report)
### set the output filename
#trajectoryTask.getReport().setTarget("copasi-benchmark-results-" + file_name + ".txt")
### don't append output if the file exists, but overwrite the file
#trajectoryTask.getReport().setAppend(False)

# get the problem for the task to set some parameters
problem = trajectoryTask.getProblem()
assert (isinstance(problem, CTrajectoryProblem))

# simulate 100 steps
problem.setStepNumber(100)
# start at time 0
datamodel.getModel().setInitialTime(0.0)
# simulate a duration of 10 time units
problem.setDuration(50)
# tell the problem to actually generate time series data
problem.setTimeSeriesRequested(True)
# tell the problem, that we want exactly 100 simulation steps (not automatically controlled)
problem.setAutomaticStepSize(False)
# tell the problem, that we don't want additional output points for event assignments
problem.setOutputEvent(False)

# set some parameters for the LSODA method through the method
method = trajectoryTask.getMethod()

parameter = method.getParameter("Absolute Tolerance")
assert parameter is not None
print(parameter.getType())
parameter.setValue(1.0e-9)

parameter = method.getParameter("Relative Tolerance")
assert parameter is not None
print(parameter.getType())
parameter.setValue(1.0e-12)

times = []

try:
  # now we run the actual trajectory
  for i in range(100):
    start = time.time()
    result = trajectoryTask.process(True)
    end = time.time()
    print(end - start)
    times.append(end - start)
except:
  sys.stderr.write("Error. Running the time course simulation failed.\n")
  # check if there are additional error messages
  if CCopasiMessage.size() > 0:
      # print the messages in chronological order
      sys.stderr.write(CCopasiMessage.getAllMessageText(True))
if not result:
  sys.stderr.write("Error. Running the time course simulation failed.\n" )
  # check if there are additional error messages
  if CCopasiMessage.size() > 0:
      # print the messages in chronological order
      sys.stderr.write(CCopasiMessage.getAllMessageText(True))

time_file = open("copasi-benchmark-times-" + file_name + ".txt", "w")
for t in times:
    time_file.write("%.14f\n" % t)

#print_results(trajectoryTask)
