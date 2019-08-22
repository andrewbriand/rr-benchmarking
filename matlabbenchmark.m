disp(3+3)
options = odeset('RelTol',1e-12,'AbsTol',1e-9);
times = zeros(1, 100);

for i = 1:100
    tic
    [timeCourse, x, rInfo] = egfr_ground(linspace(0,50,100),@ode15s,options);
    t = toc;
    if(i == 1)
        fileID = fopen("matlab-benchmark-results-egfr_ground_sbml-ode15s.txt", "w+");
        for c = x
            fprintf(fileID, "%.14f\n", c);
        end
        fclose(fileID);
    end
    disp(i);
    disp(t);
    times(i) = t;
end
fileID = fopen("matlab-benchmark-times-egfr_ground_sbml-ode15s.txt", "w+");
fprintf(fileID, "%.14f\n", times);
fclose(fileID);
