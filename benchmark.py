import sys
import time
import os
import subprocess
import platform

sbml_files = []
simulators = []
output_dir = "."
trials = 100
reltol = 1e-12
abstol = 1e-9
time_start = 0
time_end = 50
steps = 100


def roadrunner_benchmark():
    time_map = {}
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
        times = []
        for i in range(trials):
            start = time.time()
            rr.reset()
            rr.simulate(time_start, time_end, steps)
            end = time.time()
            times.append(end - start)
        time_map[file_name] = times
    return time_map


def copasi_benchmark():
    time_map = {}
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
        problem.setStepNumber(steps)
        # start at time 0
        datamodel.getModel().setInitialTime(time_start)
        # simulate a duration of 10 time units
        problem.setDuration(time_end - time_start)
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
        parameter.setValue(abstol)

        parameter = method.getParameter("Relative Tolerance")
        assert parameter is not None
        parameter.setValue(reltol)

        try:
            times = []
            # now we run the actual trajectory
            for i in range(trials):
                start = time.time()
                result = trajectoryTask.process(True)
                end = time.time()
                times.append(end - start)
            time_map[file_name] = times
        except:
            sys.stderr.write(
                "Error. Running the time course simulation failed.\n")
            # check if there are additional error messages
            if CCopasiMessage.size() > 0:
                # print the messages in chronological order
                sys.stderr.write(CCopasiMessage.getAllMessageText(True))
        if not result:
            sys.stderr.write(
                "Error. Running the time course simulation failed.\n")
            # check if there are additional error messages
            if CCopasiMessage.size() > 0:
                # print the messages in chronological order
                sys.stderr.write(CCopasiMessage.getAllMessageText(True))
    return time_map


def print_usage():
    print("Usage:")
    print("\t-files\t\tSpecify SBML files separated by spaces to benchmark on")
    print("\t-sims\t\tSpecify which simulators should be benchmarked. Currently supported are roadrunner, sbml2matlab and copasi")
    print("\t-output_dir\tSpecify which directory output files should be written to")
    print("\t-trials\t\tSpecify the number of trials to run with each simulator")
    print("\t-start\t\tSpecify the start time of each simulation to be run")
    print("\t-end\t\tSpecify the end time of each simulation to be run")
    print("\t-steps\t\tSpecify the number of steps to be run in each simulation")
    print("\t-reltol\t\tSpecify the relative tolerance for integrators used in simulation. Default is 1e-12")
    print("\t-abstol\t\tSpecify the absolute tolerance for integrators used in simulation. Default is 1e-9")
    print("\t-help\t\tPrint this help message")
    print("Example: " +
          sys.argv[0] + " -files test-sbml.xml -sims roadrunner sbml2matlab")
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
        elif(option == "trials"):
            mode = "trials"
        elif(option == "start"):
            mode = "start"
        elif(option == "end"):
            mode = "end"
        elif(option == "reltol"):
            mode = "reltol"
        elif(option == "steps"):
            mode = "steps"
        elif(option == "abstol"):
            mode = "abstol"
        elif(option == "help" or option == "h"):
            print_usage()
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
        elif(mode == "trials"):
            try:
                trials = int(arg)
            except Exception as e:
                print("Invalid argument to trials:")
                print(e)
            mode = None
        elif(mode == "steps"):
            try:
                steps = int(arg)
            except Exception as e:
                print("Invalid argument to steps:")
                print(e)
            mode = None
        elif(mode == "reltol"):
            try:
                reltol = float(arg)
            except Exception as e:
                print("Invalid argument to reltol:")
                print(e)
            mode = None
        elif(mode == "abstol"):
            try:
                abstol = float(arg)
            except Exception as e:
                print("Invalid argument to abstol:")
                print(e)
            mode = None
        elif(mode == "start"):
            try:
                time_start = float(arg)
            except Exception as e:
                print("Invalid argument to start:")
                print(e)
            mode = None
        elif(mode == "end"):
            try:
                time_end = float(arg)
            except Exception as e:
                print("Invalid argument to end")
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

if(output_dir == ""):
    print("No output directory specified, resorting to working directory")

os.makedirs(output_dir, exist_ok=True)
time_map = {}

for sim in simulators:
    if(sim == "roadrunner"):
        time_map[sim] = roadrunner_benchmark()
    elif(sim == "copasi"):
        try:
            from COPASI import *
        except Exception as e:
            print("Failed to import COPASI:")
            print(e)
        time_map[sim] = copasi_benchmark()
    elif(sim == "sbml2matlab"):
        try:
            import sbml2matlab
        except Exception as e:
            print("Failed to import sbml2matlab:")
            print(e)
        try:
            import matlab.engine
        except Exception as e:
            print("Failed to import matlab:")
            print(e)
        time_map[sim] = {}
        for file_name in sbml_files:
            print("Benchmarking sbml2matlab: " + file_name)
            sbml_file = open(file_name)
            sbml = sbml_file.read()
            matlab_code = sbml2matlab.sbml2matlab(sbml)
            sbml_file.close()
            first_paren = 0
            while matlab_code[first_paren] != "(":
                first_paren += 1
            model_name_begin = first_paren
            while matlab_code[model_name_begin] != " ":
                model_name_begin -= 1
            model_name_begin += 1
            model_name = matlab_code[model_name_begin:first_paren]
            matlab_code = "function [time] = temp()\n\t options = odeset('RelTol'," + str(reltol) + ",'AbsTol'," + str(abstol) + "); tic;\n" + \
                "\t{}(linspace({},{},{}), @ode15s, options); time = toc;\n".format(
                    model_name, time_start, time_end, steps) + matlab_code
            fid = open("temp.m", "w+")
            fid.write(matlab_code)
            fid.close()
            times = []
            eng = matlab.engine.start_matlab()
            # Run the function once to allow matlab to JIT it, for a fair
            # comparison to libroadrunner
            throwaway_time = eng.eval("temp")
            for i in range(trials):
                times.append(eng.eval("temp"))
            time_map[sim][file_name] = times

for file_name in sbml_files:
    output_file = open(output_dir + "/" + file_name + "-benchmark.csv", "w+")
    output = "Absolute tolerance:,," + str(abstol) + ",,Platform:," + platform.platform(
    ) + ",,,Processor:,," + platform.processor().replace(",", " ") + "\n"
    output += "Relative tolerance:,," + \
        str(reltol) + ",,File:," + file_name + "\n"
    output += "start:," + str(time_start) + ",end:," + \
        str(time_end) + ",steps:," + str(steps) + "\n"
    output += "\n"
    for sim in time_map.keys():
        output += sim + " average:,,," + \
            str(sum(time_map[sim][file_name])/trials) + "\n"
        output += sim + " minimum:,,," + \
            str(min(time_map[sim][file_name])) + "\n"
        output += "\n"

    for sim in time_map.keys():
        output += sim + ","
    output += "\n"
    for i in range(trials):
        for sim in time_map.keys():
            output += str(time_map[sim][file_name][i]) + ","
        output += "\n"
    output_file.write(output)
    output_file.close()
