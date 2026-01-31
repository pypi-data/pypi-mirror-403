class CompilerConfig:
    def __init__(self, stack_size: int = 1024 * 256):
        self.first_program_stack_heap_address = 0
        self.program_stack_limit = self.first_program_stack_heap_address + stack_size
        self.heap_counter = self.program_stack_limit + 1
        self.free_heap_start = self.heap_counter + 1

        self.stack_overflow_guard = True
