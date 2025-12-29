




#trung- ui
    def show_start_button(self):
        if hasattr(self, 'start_btn'):
            return
        self.start_btn = Button(self.make_canvas, text="BẮT ĐẦU", 
                               bg="green", fg="white", font=("Arial", 16, "bold"),
                               command=self.start_game)
        self.start_btn.place(x=320, y=280)