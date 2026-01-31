from ...whitespace.printstr import print_str
from ...whitespace.snippets import (
    COPY,
    DUPLICATE,
    END,
    LABEL,
    PRINT_NUMBER,
    PUSH,
    RETURN,
    SLIDE,
    STORE,
)
from ..context import EvaluationContext, IssueLevel
from ..context.evaluation_context import increment_stack, reset_stack
from ..context.stack.helpers import (
    enter_new_stack,
    exit_stack,
    exit_stack_preserve_top,
    get_datastack_location,
    silently_allocate_on_datastack,
)
from ..debugstatement import debug_instructions
from ..definitions.function import FunctionSignature
from ..expressions.expression import Expression
from ..types.primitives.void import VoidType
from .statement import Statement


class FunctionBodyStatement(Statement):

    def __init__(self, signature: FunctionSignature, body: Statement) -> None:
        super().__init__()
        self._signature = signature
        self._body = body

    def __repr__(self):
        res = f"{self._signature.return_type} "
        res += f"{self._signature.name}("
        res += ", ".join(str(param.name) for param in self._signature.parameters)
        res += f") {self._body}"
        return res

    def evaluate(self, context: EvaluationContext) -> str:
        entry_label = context.label_registry.new_label()
        context.function_registry.register_function(self._signature, entry_label)

        # Stack frame and initial variables are set up by the caller.
        # We just need to generate the body here.

        res = LABEL(entry_label)
        res += debug_instructions(print_str("Entering function: " + self._signature.name + "\n"))
        param_count = len(self._signature.parameters)

        # The caller pushed: [ds_caller_copy, param0, param1, ...]
        # So ds_caller_copy is at offset param_count from the top
        with increment_stack(context, param_count):
            res += enter_new_stack(context)

        with reset_stack(context):
            # Allocate space for function variables
            total_var_size = sum(v.type.get_size() for v in self._signature.variables)
            res += silently_allocate_on_datastack(context, total_var_size)

            # At this point the stack should be set up as follows:
            # ...
            # Last stack frame pointer
            # Parameter 0
            # Parameter 1
            # ...
            # Parameter N
            # New stack frame pointer

            # Store parameters into their respective variables
            for i, param in enumerate(self._signature.parameters):
                matching_var = self._signature.get_variable(param.name)
                if not matching_var:
                    raise Exception(f"Parameter {param.name} not found in function variables.")
                res += get_datastack_location(context, matching_var.offset)
                # Stack: [..., ds_caller_copy, params..., new_ds, var_addr]
                # Need to copy param at position: 1 (var_addr) + 1 (new_ds) + (param_count - i - 1)
                res += COPY(1 + 1 + (param_count - i - 1))
                res += STORE
            # Slide off all params AND the ds_caller_copy
            res += SLIDE(param_count + 1)

            with context.function_registry.function_context(self._signature):
                res += self._body.evaluate(context)

                if self._signature.return_type == VoidType():
                    res += ReturnStatement(None).evaluate(context)
                else:
                    # Non-void functions should return a value before reaching the end.
                    # If the function body reaches here, it's an error in the source code.
                    # TODO: Optimize this error by only having it once in the program, and jumping to it.
                    res += print_str("Error: Non-void function did not return a value.\n")
                    res += END

        return res


class ReturnStatement(Statement):

    def __init__(self, value: Expression | None):
        super().__init__()
        self._value = value

    def __repr__(self):
        if self._value is None:
            return "return"
        return f"return {self._value}"

    def evaluate(self, context: EvaluationContext) -> str:
        if not context.function_registry.current_function:
            context.register_issue(
                IssueLevel.ERROR,
                self,
                "Return statement outside of a function.",
            )
            return ""
        function_definition = context.function_registry.current_function

        if function_definition.return_type == VoidType():
            if self._value is not None:
                context.register_issue(
                    IssueLevel.ERROR,
                    self,
                    "Void function should not return a value.",
                )
                return ""

            res = exit_stack(context)
            res += PUSH(0)  # Void functions must also leave a value on the stack
            res += RETURN
            return res
        else:
            if self._value is None:
                context.register_issue(
                    IssueLevel.ERROR,
                    self,
                    "Non-void function must return a value.",
                )
                return ""
            value_type = self._value.get_type(context)
            if value_type != function_definition.return_type:
                context.register_issue(
                    IssueLevel.ERROR,
                    self,
                    f"Return type mismatch: expected {function_definition.return_type}, "
                    f"got {value_type}.",
                )
                return ""

            # Evaluate the return value
            res = self._value.evaluate(context)

            res += debug_instructions(
                print_str("Returning value: ") + DUPLICATE + PRINT_NUMBER + print_str("\n")
            )

            # Exit the function stack frame
            res += exit_stack_preserve_top(context)

            # Return from the function
            res += RETURN
            return res
