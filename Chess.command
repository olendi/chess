#!/usr/bin/env python

import ui

app = ui.Chess()
app.master.title('Baba Chess')

app.master.attributes('-topmost', True)
app.master.update()
app.master.attributes('-topmost', False)

app.mainloop()
