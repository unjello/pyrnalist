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

def progress_render_thread(current, total, delay, chars):
    while True:
        columns = os.get_terminal_size().columns
        ratio = current.value / total
        ratio = min(max(ratio, 0), 1)
        stat = f' {current.value}/{total}'
        available_space = max(0, columns - len(stat) - 3)
        width = min(total, available_space)
        complete_length = round(width * ratio)
        complete = chars[0] * complete_length
        incomplete = chars[1] * (width - complete_length)
        bar = f'[{complete}{incomplete}]{stat}'
        print(f"\r{bar}", end="", flush=True)
        time.sleep(delay)

BARS = [['#', '-']]
class ProgressBar:
    def __init__(self, steps_count):
        self.total = steps_count
        self.delay = 0.06
        self.chars = BARS[0]
        self.manager = multiprocessing.Manager()
        self.current = self.manager.Value(ctypes.c_int64, 0)

    def start(self):
        self.__thread = multiprocessing.Process(
            target=progress_render_thread,
            args=(
                self.current,
                self.total,
                self.delay,
                self.chars
            ),
        )
        self.__thread.start()

    def tick(self):
        if self.current.value >= self.total:
            return
        
        self.current.value += 1


    def stop(self):
        self.__thread.terminate()


class BaseReporter:
    def __init__(self, verbose=True, silent=False, emoji=True, no_progress=False):
        self.is_verbose = verbose
        self.is_silent = silent
        self.emoji = emoji
        self.no_progess = no_progress
        self._log_category_size = 0
        self._spinners = set()
        self._progress_bar = None

    def verbose(self, text):
        if self.is_verbose:
            self._verbose(text)

    def activity(self):
        if self.is_silent:
            return NullSpinnerReporter()

        reporters = self._spinners
        spinner = self._get_spinner()
        spinner.start()
        reporters.add(spinner)
        return SpinnerReporter(spinner, reporters)

    def progress(self, steps_count):
        def null_progress_tick():
            pass

        if self.no_progess or steps_count <= 0:
            return null_progress_tick

        if self.is_silent:
            return null_progress_tick

        self._stop_progress()

        self._progress_bar = ProgressBar(steps_count)
        self._progress_bar.start()

        return lambda: self._progress_bar.tick()

    def _stop_progress(self):
        if self._progress_bar:
            self._progress_bar.stop()

    def _get_emoji(self, emoji):
        if self.is_silent or not self.emoji:
            return ""

        return emoji

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
    def __init__(self, verbose=True, silent=False, emoji=True, no_progress=False):
        BaseReporter.__init__(self, verbose, silent, emoji, no_progress)

    def list(self, title, items, hints={}):
        self._log_category("list", title, style=Fore.LIGHTMAGENTA_EX + Style.BRIGHT)
        gutter_width = (self._log_category_size or 2) - 1
        gutter = " " * gutter_width
        if len(hints.keys()) == len(items):
            for item in items:
                self._log(f"{gutter}- " + Style.BRIGHT + f"{item}" + Style.RESET_ALL)
                hint = hints.get(item, None)
                if hint:
                    self._log(f" {gutter} " + Style.DIM + f"{hint}" + Style.RESET_ALL)
        else:
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

    def header(self, name, command=None, version=None):
        command = f" {command}" if command else ""
        version = f" v{version}" if version else ""
        self.log(Style.BRIGHT + Fore.WHITE + f"{name}{command}{version}")

    def footer(self):
        self._stop_progress()
        total_time = get_uptime()
        emoji = self._get_emoji("✨")
        emoji = f"{emoji} " if emoji else ""
        self.log(f"{emoji}Done in {total_time}s")

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

    def _get_spinner(self):
        return ConsoleSpinner()


def create_reporter(verbose=True, silent=False, emoji=True, no_progress=False):
    init(autoreset=True)
    return ConsoleReporter(verbose, silent, emoji, no_progress)


report = create_reporter()


if __name__ == "__main__":
    import time

    report.header("pyrnalist", version="0.0.7")

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

    steps = 15
    tick = report.progress(steps)
    report.info('🥚 Wait for it...')
    for x in range(steps):
        tick()
        if x % 5 == 0:
            report.warn("Interrupt.")
        time.sleep(0.25)
    report.success('🐣 Tjiep!')

    report.list('My grocery list', ['bananas', 'tulips', 'eggs', 'bamischijf'])

    items = ['bananas', 'tulips', 'eggs', 'bamischijf']
    hints = {
        'bananas': 'for baking',
        'tulips': 'because it makes you happy',
        'eggs': 'not the cheap ones though',
        'bamischijf': 'if they have it',
    }
    report.list('My grocery list', items, hints)

    report.footer()
