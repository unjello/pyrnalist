from re import S
from colorama import init, Style, Fore, Back, ansi
from datetime import datetime
import os
import sys
import time
import psutil
import multiprocessing
import ctypes


def get_start_time():
    pid = os.getpid()
    p = psutil.Process(pid)
    return datetime.fromtimestamp(p.create_time())


def get_uptime():
    return float((datetime.now() - get_start_time()).total_seconds())


class NullSpinnerReporter:
    def tick(self, name):
        pass

    def end(self):
        pass


class SpinnerReporter:
    def __init__(self, spinner, reporters):
        self.reporters = reporters
        self.spinner = spinner

    def tick(self, name):
        self.spinner.set_text(name)

    def end(self):
        self.spinner.stop()
        self.reporters.remove(self.spinner)


SPINNERS = [
    "|/-\\",
    "⠂-–—–-",
    "◐◓◑◒",
    "◴◷◶◵",
    "◰◳◲◱",
    "▖▘▝▗",
    "■□▪▫",
    "▌▀▐▄",
    "▉▊▋▌▍▎▏▎▍▌▋▊▉",
    "▁▃▄▅▆▇█▇▆▅▄▃",
    "←↖↑↗→↘↓↙",
    "┤┘┴└├┌┬┐",
    "◢◣◤◥",
    ".oO°Oo.",
    ".oO@*",
    "🌍🌎🌏",
    "◡◡ ⊙⊙ ◠◠",
    "☱☲☴",
    "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
    "⠋⠙⠚⠞⠖⠦⠴⠲⠳⠓",
    "⠄⠆⠇⠋⠙⠸⠰⠠⠰⠸⠙⠋⠇⠆",
    "⠋⠙⠚⠒⠂⠂⠒⠲⠴⠦⠖⠒⠐⠐⠒⠓⠋",
    "⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠴⠲⠒⠂⠂⠒⠚⠙⠉⠁",
    "⠈⠉⠋⠓⠒⠐⠐⠒⠖⠦⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈",
    "⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈",
    "⢄⢂⢁⡁⡈⡐⡠",
    "⢹⢺⢼⣸⣇⡧⡗⡏",
    "⣾⣽⣻⢿⡿⣟⣯⣷",
    "⠁⠂⠄⡀⢀⠠⠐⠈",
]


def spinner_render_thread(id, delay, text):
    current = 0
    chars = [char for char in SPINNERS[id]]
    chars_len = len(chars)
    while True:
        t = text.value
        print(f"\r{chars[current]} {t}", end="", flush=True)
        current = (current + 1) % chars_len
        time.sleep(delay)


class ConsoleSpinner:
    def __init__(self):
        self.spinner_id = 28
        self.delay = 0.06
        self.manager = multiprocessing.Manager()
        self.text = self.manager.Value(ctypes.c_wchar_p, "")

    def start(self):
        self.__thread = multiprocessing.Process(
            target=spinner_render_thread,
            args=(
                self.spinner_id,
                self.delay,
                self.text,
            ),
        )
        self.__thread.start()

    def stop(self):
        self.__thread.terminate()

    def set_text(self, text):
        self.text.value = text


class BaseReporter:
    def __init__(self, verbose=True, silent=False, emoji=True):
        self.is_verbose = verbose
        self.is_silent = silent
        self.emoji = emoji
        self._log_category_size = 0
        self._spinners = set()

    def verbose(self, text):
        if self.is_verbose:
            self._verbose(text)

    def activity(self):
        if self.is_silent:
            return NullSpinnerReporter()

        reporters = self._spinners
        spinner = ConsoleSpinner()
        spinner.start()
        reporters.add(spinner)
        return SpinnerReporter(spinner, reporters)

    def _log(
        self,
        text,
        force=False,
        out=sys.stdout,
    ):
        if self.is_silent and not force:
            return

        print(f"\r{ansi.clear_line() + text + Style.RESET_ALL}", file=out)


class ConsoleReporter(BaseReporter):
    def __init__(self, verbose=True, silent=False, emoji=True):
        BaseReporter.__init__(self, verbose, silent, emoji)

    def list(self, title, items):
        self._log_category("list", title, style=Fore.LIGHTMAGENTA_EX + Style.BRIGHT)
        gutter_width = (self._log_category_size or 2) - 1
        gutter = " " * gutter_width
        for item in items:
            self._log(f"{gutter}- {item}")

    def command(self, text):
        self.log(Style.DIM + f"$ {text}")

    def success(self, text):
        self._log_category("success", text, style=Fore.GREEN)

    def error(self, text):
        print(
            ansi.clear_line() + Fore.RED + "error" + Fore.RESET + f" {text}",
            file=sys.stderr,
        )

    def info(self, text):
        self._log_category("info", text, style=Fore.BLUE)

    def warn(self, text):
        self._log_category("warning", text, style=Fore.YELLOW)

    def log(self, text):
        self._log_category_size = 0
        self._log(text)

    def _log_category(self, category, text, style):
        self._log_category_size = len(category)
        self._log(style + category + Style.RESET_ALL + f" {text}")

    def _verbose(self, text):
        uptime = get_uptime()
        self._log_category("verbose", f"{uptime} {text}", style=Style.DIM)


def create_reporter(verbose=True, silent=False, emoji=True):
    init(autoreset=True)
    return ConsoleReporter(verbose, silent, emoji)


report = create_reporter()


if __name__ == "__main__":
    import time

    report.info("Please wait while I fetch something for you.")
    report.warn("It might take a little while though.")

    spinner = report.activity()
    spinner.tick("I am on it!")
    time.sleep(1)
    spinner.tick("Still busy...")
    time.sleep(1)
    spinner.tick("Almost there...")
    time.sleep(1)
    report.success("Done!")
    spinner.end()
