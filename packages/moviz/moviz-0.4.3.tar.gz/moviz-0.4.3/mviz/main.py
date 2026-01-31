from termcolor import cprint
from mviz.viser_tools import BaseVisualizer
from mviz import ROOT_DIR

def main():
    visualizer = BaseVisualizer(target_fps=100.0)
    visualizer.auto_register_plugins()
    visualizer.create_module_selector()
    visualizer.set_active_module("Motion Loader")
    visualizer.main_loop()

if __name__ == "__main__":
    main()
