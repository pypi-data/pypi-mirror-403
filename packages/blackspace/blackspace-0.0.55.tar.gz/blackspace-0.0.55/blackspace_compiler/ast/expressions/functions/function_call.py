from ....whitespace.snippets import CALL, COPY
from ...context import EvaluationContext, IssueLevel
from ...context.evaluation_context import increment_stack
from ...debugstatement import debug_statement
from ...types.primitives.void import VoidType
from ..expression import Expression


class FunctionCall(Expression):
    def __init__(self, name: str, parameters: list[Expression]) -> None:
        super().__init__()
        self._name = name
        self._parameters = parameters

    def __repr__(self):
        return f"{self._name}(" + ", ".join(repr(p) for p in self._parameters) + ")"

    def get_type(self, context):
        function_def = context.function_registry.get_function_definition(self._name)
        if function_def:
            return function_def.return_type
        else:
            return VoidType()

    def evaluate(self, context: EvaluationContext) -> str:
        function_def = context.function_registry.get_function_definition(self._name)
        if not function_def:
            context.register_issue(
                IssueLevel.ERROR,
                self,
                f"Function '{self._name}' is not defined.",
            )
            return ""

        if len(function_def.parameters) != len(self._parameters):
            context.register_issue(
                IssueLevel.ERROR,
                self,
                f"Function '{self._name}' expects {len(function_def.parameters)} parameters, "
                f"but {len(self._parameters)} were given.",
            )
            return ""

        for i in range(min(len(self._parameters), len(function_def.parameters))):
            expected_type = function_def.parameters[i].type
            actual_type = self._parameters[i].get_type(context)
            if actual_type != expected_type:
                context.register_issue(
                    IssueLevel.ERROR,
                    self,
                    f"Parameter {i + 1} of function '{self._name}' expects type "
                    f"'{expected_type}', but got type '{actual_type}'.",
                )
                return ""

        function_label = context.function_registry.get_function_label(self._name)

        res = ""
        res += debug_statement("Function call: " + self._name)

        # Copy the current datastack pointer onto the stack BEFORE parameters.
        # This ensures the callee can find the caller's datastack at a fixed
        # offset (param_count) regardless of how deep the expression stack is.
        res += COPY(context.stack_offset)

        # Evaluate parameters onto the stack
        # Each parameter needs to account for the copied datastack ptr (+1)
        # and previously evaluated parameters
        for i, param in enumerate(self._parameters):
            with increment_stack(context, 1 + i):  # +1 for the copied datastack ptr
                res += param.evaluate(context)

        # Call function
        res += CALL(function_label)

        # The function return value should be on the stack as per calling convention.
        # This exactly matches how expressions work, so no extra handling is needed.
        return res
