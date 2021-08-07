from pprint import pformat
import logging
import laboratory
import types


class LoggingExperiment(laboratory.Experiment):
    def publish(self, result):
        if not result.match:
            try:
                logging.error(f"Experiment mismatch: output from {result.candidates[0].name} did not match {result.control.name}",
                    extra={
                        'custom_dimensions': {
                            'expected_value': pformat(result.control.value),
                            'actual_value': pformat(result.candidates[0].value),
                            'actual_exception': pformat(result.candidates[0].exception),
                        }
                    })
            except Exception as e:
                # if the detailed reporting fails for some reason, make sure we fall back to something
                # simpler that won't throw and interfere with the rest of the app
                logging.error("Experiment mismatch!: " + pformat(result), extra={'custom_dimensions': {'exception': pformat(e)}})


def method_missing(method_name, type_name):
    raise Exception(f"{method_name} not implemented on {type_name}")


def make_experiment_object(control, candidate):
    # inspect the control object to find the set of methods we want to experiment on
    api_methods = [
        getattr(control, a)
        for a in dir(control)
        if (not a.startswith("__")) and callable(getattr(control, a))
    ]

    # create a dynamic object to hold the experiment methods
    result = types.SimpleNamespace()

    for api_method in api_methods:
        # find the matching method on the candidate object, if it exists
        candidate_method = getattr(
            candidate,
            api_method.__name__,
            lambda *args, **kwargs: method_missing(
                api_method.__name__, type(candidate).__name__
            ),
        )

        # https://stackoverflow.com/a/3431699 double function to avoid closure issues
        def make_experiment_method(api_method, candidate_method):
            def create_and_run_experiment(*args, **kwargs):
                experiment = LoggingExperiment()
                experiment.control(
                    api_method,
                    args,
                    kwargs,
                    name=f"{type(control).__name__}.{api_method.__name__}",
                )
                experiment.candidate(
                    candidate_method,
                    args,
                    kwargs,
                    name=f"{type(candidate).__name__}.{api_method.__name__}",
                )
                return experiment.conduct()

            return create_and_run_experiment

        # now add the generated method to the result
        setattr(
            result,
            api_method.__name__,
            make_experiment_method(api_method, candidate_method),
        )

    return result
