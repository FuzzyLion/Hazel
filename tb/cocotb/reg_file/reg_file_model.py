class RegFileModel():
    def __init__(self):
        self.regs = [0] * 32
    def on_rising_edge(self, reset, we, rd, data):
        if reset == 1:
            for idx in range(len(self.regs)):
                self.regs[idx] = 0
        else:
            if we and rd != 0:
                self.regs[rd] = data
    def read(self, rs, we, rd, data):
        if rs == 0:
            rs_val = 0
        elif we and rs == rd:
            rs_val = data
        else:
            rs_val = self.regs[rs]

        return rs_val
        