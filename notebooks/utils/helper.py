import os
import yaml
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import dspy


def file_exists(file_path):
    return os.path.exists(file_path)

def load_cache(file_path):
    if file_exists(file_path):
        dspy.cache.load_memory_cache(file_path)
    else:
        print(f"Cache file {file_path} not found.")

def save_cache(file_path, overwrite=False):
    if file_exists(file_path) and not overwrite:
        print(f"Cache file {file_path} already exists. Use overwrite=True to overwrite.")
        return
    else:
        dspy.cache.save_memory_cache(file_path)



# these expect to find a .env file at the directory above the lesson.    # the format for that file is (without the comment)                      #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService
def load_env():
    _ = load_dotenv(find_dotenv())

def get_api_key(name):
    load_env()
    api_key = os.getenv(name)
    return api_key


def load_data(file_path):
    """
    Load yaml file
    :param file_path:
    :return:
    """
    with open(file_path, 'r') as file:
        ds = yaml.safe_load(file)
    return ds


def validate_prediction(content, test_case):
    """Validate the prediction"""
    r = run_test_case(content, test_case)
    score_map = {
        "passed": 1.0,
        "assertion_failed": 0.5,
        "runtime_error": 0.25,
        "syntax_error": 0.0
    }
    feedback_map = {
        "passed": "Code executed successfully and passed all tests.",
        "assertion_failed": "Code runs but produces incorrect output.",
        "runtime_error": f"Runtime error: {r.get('error', 'Unknown error')}",
        "syntax_error": f"Syntax error at line {r.get('line', '?')}: {r.get('error', 'Unknown error')}"
    }
    score = score_map.get(r["status"], 0)
    feedback = feedback_map.get(r["status"], "Unknown error")
    return score, feedback


def run_test_case(content, test_case):
    """Compile and execute with better error tracking"""
    namespace = {}

    try:
        # Compile and execute the main code
        code_obj = compile(content, '<content>', 'exec')
        exec(code_obj, namespace)

        # Compile and execute the test
        test_obj = compile(test_case, '<test_case>', 'exec')
        exec(test_obj, namespace)

        return {"status": "passed"}
    except SyntaxError as e:
        return {
            "status": "syntax_error",
            "error": str(e),
            "line": e.lineno,
            "text": e.text
        }
    except AssertionError as e:
        return {"status": "assertion_failed", "error": str(e) or "Assertion failed"}
    except Exception as e:
        return {"status": "runtime_error", "error": f"{type(e).__name__}: {str(e)}"}


class ExperimentStats:
    def __init__(self, dataset):
        self.ds = dataset
        self.experiments = {}

    def add_experiment(self, experiment_name, experiment):
        self.experiments[experiment_name] = experiment

    def get_stats(self):
        columns = ["name"]
        names = []
        col_data = {"name": names}
        for el in self.ds:
            names.append(el["name"])
        names.append("Experiment score, %")
        for experiment_name, experiment in self.experiments.items():
            columns.append(experiment_name)
            score, results = experiment.score, experiment.results
            lst = []
            for tpl in results:
                el, pred, score_row = tpl
                lst.append(score_row)
            lst.append(score)
            col_data[experiment_name] = lst

        df = pd.DataFrame(col_data)

        return df
