import sys
import time
import os
import subprocess

sbml_files = []
simulators = []
output_dir = ""
matlab_executable = ""
matlab_command = "{} -nodisplay -nosplash -nodesktop -r \"try, options = odeset('RelTol',1e-12,'AbsTol',1e-9); tic; {}(linspace(0,50,100), @ode15s, options); catch me, disp(me.message); end\""
matlab_time_format = "\"%.14f\""
trials = 100

def roadrunner_benchmark():
    try:
        import roadrunner
        print("libroadrunner version: " + roadrunner.__version__)
    except Exception as e:
        print("Failed to import roadrunner:")
        print(e)
    for file_name in sbml_files:
        print("Benchmarking libroadrunner: " + file_name)
        rr = roadrunner.RoadRunner(file_name)
        rr.getIntegrator().setValue("absolute_tolerance", 1e-9)
        rr.getIntegrator().setValue("relative_tolerance", 1e-12)
        for i in range(trials):
            start = time.time()
            rr.reset()
            rr.simulate(0, 50, 100)
            end = time.time()
            times.append(end - start)

def copasi_benchmark():
    for file_name in sbml_files:
        print("Benchmarking COPASI: " + file_name)
        datamodel = CRootContainer.addDatamodel()

        sbml_file = open(file_name, "r")
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
        parameter.setValue(1.0e-9)

        parameter = method.getParameter("Relative Tolerance")
        assert parameter is not None
        parameter.setValue(1.0e-12)

        try:
          # now we run the actual trajectory
          for i in range(trials):
            start = time.time()
            result = trajectoryTask.process(True)
            end = time.time()
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



def print_usage():
    print("Usage:")
    print("[-files [sbml files to benchmark with]] [-sims [simulators to test]]")
    print("Example: " + sys.argv[0] + " -files test-sbml.xml -sims roadrunner sbml2matlab")
    sys.exit()

mode = None
for arg in sys.argv[1:]:
    if(arg[0] == "-"):
        option = arg[1:]
        if(option == "files"):
            mode = "files"
        elif(option == "sims"):
            mode = "sims"
        elif(option == "output_dir"):
            mode = "output_dir"
        elif(option == "matlab_exe"):
            mode = "matlab_exe"
        elif(option == "trials"):
            mode = "trials"
        else:
            print("Unrecognized option: " + option)
            print_usage()
    else:
        if(mode == "sims"):
            simulators.append(arg)
        elif(mode == "files"):
            sbml_files.append(arg)
        elif(mode == "output_dir"):
            output_dir = arg
            mode = None
        elif(mode == "matlab_exe"):
            matlab_executable = arg
            mode = None
        elif(mode == "trials"):
            try:
                trials = int(arg)
            except Exception as e:
                print("Invalid argument to trials:")
                print(e)
            mode = None
        else:
            print("Expected an option, got: " + arg)
            print_usage()

if(len(sbml_files) == 0):
    sbml_files = ["small-test-sbml.xml", "egfr_ground_sbml.xml"]
    print("No sbml files specified, resorting to defaults:")
    print(sbml_files)

if(len(simulators) == 0):
    simulators = ["sbml2matlab", "roadrunner", "copasi"]
    print("No simulators specified, resorting to defaults:")
    print(simulators)

if "sbml2matlab" in simulators:
    if matlab_executable == "":
        matlab_executable = "matlab"
        print("No matlab executable specified, resorting to default:")
        print(matlab_executable)

if(output_dir == ""):
    print("No output directory specified, resorting to working directory")

time_map = {}
for file_name in sbml_files:
    time_map[file_name] = {}

for sim in simulators:
    times = []
    if(sim == "roadrunner"):
        roadrunner_benchmark()
    elif(sim == "copasi"):
        try:
            from COPASI import *
        except Exception as e:
            print("Failed to import COPASI:")
            print(e)
        copasi_benchmark()
    elif(sim == "sbml2matlab"):
        try:
            import sbml2matlab
        except Exception as e:
            print("Failed to import sbml2matlab:")
            print(e)
        for file_name in sbml_files:
            print("Benchmarking sbml2matlab: " + file_name)
            sbml_file = open(file_name)
            sbml = sbml_file.read()
            matlab_code = sbml2matlab.sbml2matlab(sbml)
            sbml_file.close()
            #this is pretty terrible, should probably find a better way to get the model name
            first_paren = 0
            while matlab_code[first_paren] != "(":
                first_paren += 1
            model_name_begin = first_paren
            while matlab_code[model_name_begin] != " ":
                model_name_begin -= 1
            model_name_begin += 1
            model_name = matlab_code[model_name_begin:first_paren]
            print(model_name)
            open(output_dir + "/" + model_name + ".m", "w+").write(matlab_code)
            print(subprocess.check_output(matlab_command.format(matlab_executable, model_name, matlab_time_format)))

    time_map[file_name][sim] = times

print(time_map)

