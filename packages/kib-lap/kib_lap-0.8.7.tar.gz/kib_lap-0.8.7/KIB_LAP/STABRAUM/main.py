from Programm import mainloop
from Plotting import StructurePlotter
from Output_Data import OutputData
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


if __name__ == "__main__":
    calc = mainloop()
    res = calc.run()

    plotter = StructurePlotter(res)
    Output = OutputData()

    calc.check_global_equilibrium()


    out = OutputData()
    df = out.support_reactions_from_springs_table(res)
    print(df)

    calc.sum_reactions_fx()
    calc.sum_spring_reactions_fx()

    plotter = StructurePlotter(res)

    # Slider muss einer Variablen zugewiesen werden, sonst Garbage Collection!
    slider = plotter.plot_diagram_interactive(kind="MY", scale_init=2.0,show_loads=True)
    slider = plotter.plot_diagram_interactive(kind="MZ", scale_init=2.0,show_loads=False)
    slider = plotter.plot_diagram_interactive(kind="MX", scale_init=2.0,show_loads=False)
    slider = plotter.plot_diagram_interactive(kind="MTP", scale_init=2.0,show_loads=False)
    slider = plotter.plot_diagram_interactive(kind="MTS", scale_init=2.0,show_loads=False)



