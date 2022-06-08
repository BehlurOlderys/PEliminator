import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from gui.functions.encoder_manager import EncoderManager
from widgets.periods_list import PeriodsList
from widgets.data_aggregator import DataAggregator
from widgets.image_files_list import ImageFilesList
# from common.global_settings import settings
from widgets.fragment_displayer import FragmentDisplayer
from widgets.plotter import Plotter
from widgets.image_displayer import ImageDisplayer
from widgets.automat import Automat
from widgets.text_indicator import TextIndicator
# from gui.functions.times_generator import TimesGenerator


root = tk.Tk()
root.title("PEliminator")


current_axis = None
ax_fragment = None
image_data = None


tabs = ttk.Notebook(root)
tabs.pack(pady=10, expand=True)
image_tab = tk.Frame(tabs)
image_tab.pack(fill='both', expand=True)
tabs.add(image_tab, text="Image")

drift_plot_tab = tk.Frame(tabs)
drift_plot_tab.pack(fill='both', expand=True)
tabs.add(drift_plot_tab, text="Drift plot")

encoder_tab = tk.Frame(tabs)
encoder_tab.pack(fill='both', expand=True)
tabs.add(encoder_tab, text="Encoder data")

combine_tab = tk.Frame(tabs)
combine_tab.pack(fill='both', expand=True, side=tk.LEFT)
tabs.add(combine_tab, text="Correction")

indicators_frame = tk.Frame(combine_tab)
period_list_frame = tk.Frame(combine_tab)
period_list_frame.pack(side=tk.RIGHT)

combine_button = tk.Button(indicators_frame, text='Combine!')
combine_button.pack(side=tk.BOTTOM)

files_indicator = TextIndicator(indicators_frame, "Files loaded?")
drift_indicator = TextIndicator(indicators_frame, "Drift calculated?")
encoder_indicator = TextIndicator(indicators_frame, "Encoder data?")
indicators_frame.pack(side=tk.LEFT)

combine_figure = plt.Figure(dpi=100)
combine_ax = combine_figure.add_subplot(111)
combine_canvas = FigureCanvasTkAgg(combine_figure, combine_tab)
combine_canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

generator = TimesGenerator()

generate_new_button = tk.Button(period_list_frame, text="Generate new data", command=generator.load)
generate_new_button.pack(side=tk.BOTTOM)

save_csv_button = tk.Button(period_list_frame, text="Save to .csv")
save_csv_button.pack(side=tk.BOTTOM)

average_button = tk.Button(period_list_frame, text="Get average")
average_button.pack(side=tk.BOTTOM)

diff_button = tk.Button(period_list_frame, text="Calculate speeds")
diff_button.pack(side=tk.BOTTOM)

smooth_periods_button = tk.Button(period_list_frame, text="Smooth data")
smooth_periods_button.pack(side=tk.BOTTOM)

remove_period_button = tk.Button(period_list_frame, text="Remove selected")
remove_period_button.pack(side=tk.TOP)


periods_list = PeriodsList(period_list_frame, combine_ax, combine_canvas)

smooth_periods_button.configure(command=periods_list.smooth)
diff_button.configure(command=periods_list.calculate_speed)


def average_action():
    averaged = periods_list.average_periods()
    generator.push_errors(averaged)


average_button.configure(command=average_action)
save_csv_button.configure(command=periods_list.save_lines_to_file)
remove_period_button.configure(command=periods_list.remove)

top_frame = tk.Frame(image_tab)
bottom_frame = tk.Frame(image_tab)
progress_frame = tk.Frame(image_tab)
top_frame.pack(side=tk.TOP, expand=True)
progress_frame.pack(side=tk.BOTTOM)
bottom_frame.pack(side=tk.BOTTOM)

plot_frame = tk.Frame(drift_plot_tab)
plot_frame.pack(fill='both', expand=True)

data_aggregator = DataAggregator(files_indicator,
                                 drift_indicator,
                                 encoder_indicator,
                                 combine_button,
                                 combine_ax,
                                 combine_canvas,
                                 periods_list)

fragment_displayer = FragmentDisplayer(bottom_frame)
plotter = Plotter(plot_frame)
displayer = ImageDisplayer(top_frame, fragment_displayer, plotter)

file_list_frame = tk.Frame(bottom_frame)
file_list = ImageFilesList(file_list_frame, displayer, data_aggregator)
file_list_frame.pack(side=tk.LEFT, padx=30, pady=30)

remove_button = tk.Button(file_list_frame, text='Delete', command=file_list.remove)
remove_button.pack(side=tk.BOTTOM)

next_button = tk.Button(file_list_frame, text='Next', command=file_list.next)
next_button.pack(side=tk.TOP)

left_buttons_frame = tk.Frame(top_frame)
left_buttons_frame.pack(side=tk.LEFT)

enhance_button = tk.Button(left_buttons_frame, text='Enhance', command=displayer.enhance)
enhance_button.pack(side=tk.BOTTOM)

display_button = tk.Button(file_list_frame, text='Display', command=file_list.display_selection)
display_button.pack(side=tk.BOTTOM)

calculate_button = tk.Button(left_buttons_frame, text='Calculate', command=displayer.calculate_center)
calculate_button.pack(side=tk.BOTTOM)

progress_bar = ttk.Progressbar(
    progress_frame,
    orient='horizontal',
    mode='determinate',
    length=1000
)
progress_bar.pack(side=tk.BOTTOM, fill=tk.BOTH)

automat = Automat(root, displayer, plotter, progress_bar, file_list, data_aggregator)
encoder_manager = EncoderManager(root, encoder_tab, progress_bar, data_aggregator)

auto_button = tk.Button(left_buttons_frame, text='AUTO', command=automat.go_auto)
auto_button.pack(side=tk.BOTTOM)

load_files_button = tk.Button(left_buttons_frame, text='Load images', command=file_list.choose_dir)
load_files_button.pack(side=tk.TOP)


vis_button = tk.Button(left_buttons_frame, text='Display Off')
open_encoder_button = tk.Button(left_buttons_frame, text='Open encoder log', command=encoder_manager.get_encoder_data)
datetime_label = tk.Label(left_buttons_frame, text='<datetime>')

file_list.show_datetime_on(datetime_label)


def action_vis():
    new_setting = settings.toggle_visualisation()
    t = "Display Off" if new_setting else "Display On"
    vis_button.configure(text=t)


vis_button.configure(command=action_vis)
vis_button.pack(side=tk.BOTTOM)
open_encoder_button.pack(side=tk.BOTTOM)
datetime_label.pack(side=tk.BOTTOM)

plot_buttons_frame = tk.Frame(plot_frame)
plot_buttons_frame.pack(side=tk.RIGHT)
plot_toggle_red = tk.Button(plot_buttons_frame, text='TURN OFF', bg='red', fg='orange')


def red_action():
    plotter.toggle_red()
    b_on = plotter.get_red_state()
    new_text = 'TURN OFF' if b_on else 'TURN ON'
    print(f"new text = {new_text}")
    plot_toggle_red.configure(text=new_text)
    print("Action red!")


plot_toggle_red.configure(command=red_action)
plot_toggle_red.pack(side=tk.BOTTOM)

plot_toggle_green = tk.Button(plot_buttons_frame, text='TURN OFF', bg='green', fg='white')


def green_action():
    plotter.toggle_green()
    b_on = plotter.get_green_state()
    new_text = 'TURN OFF' if b_on else 'TURN ON'
    plot_toggle_green.configure(text=new_text)


plot_toggle_green.configure(command=green_action)
plot_toggle_green.pack(side=tk.BOTTOM)

ylim_low_value = tk.StringVar(value=0)
ylim_high_value = tk.StringVar(value=1)

ylim_frame = tk.Frame(plot_buttons_frame)
ylim_frame.pack(side=tk.BOTTOM)
ylim_low_spinbox = ttk.Spinbox(ylim_frame, from_=-1000, to=1000, textvariable=ylim_low_value, wrap=False)
ylim_low_spinbox.pack(side=tk.LEFT)
ylim_high_spinbox = ttk.Spinbox(ylim_frame, from_=-1000, to=1000, textvariable=ylim_high_value, wrap=False)
ylim_high_spinbox.pack(side=tk.RIGHT)

ylim_button = tk.Button(plot_buttons_frame, text="Set Y limit",
                        command=lambda: plotter.change_ylim(
                            (int(ylim_low_value.get()), int(ylim_high_value.get()))
                        ))
ylim_button.pack(side=tk.TOP)

root.state("zoomed")
root.mainloop()

# TODO: change encoder datetime format to be easy readible
