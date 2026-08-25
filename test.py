from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

from threading import Thread

from chat import process_message


class Chitragupt(App):

    def build(self):

        layout = BoxLayout(
            orientation="vertical"
        )

        self.chat = Label(
            text="Chitragupt: Namaste! 👋",
            halign="left",
            valign="top"
        )

        layout.add_widget(self.chat)

        bottom = BoxLayout(
            size_hint_y=0.15
        )

        self.input_box = TextInput(
            hint_text="Type your message...",
            multiline=False
        )

        send = Button(
            text="Send",
            size_hint_x=0.25
        )

        send.bind(
            on_press=self.send_message
        )

        bottom.add_widget(self.input_box)
        bottom.add_widget(send)

        layout.add_widget(bottom)

        return layout

    def send_message(self, instance):

        message = self.input_box.text.strip()

        if not message:
            return

        self.chat.text += f"\n\nYou: {message}"

        self.input_box.text = ""

        # AI ko background thread mein run karo
        Thread(
            target=self.get_reply,
            args=(message,),
            daemon=True
        ).start()

    def get_reply(self, message):

        reply = process_message(message)

        # Kivy UI ko main thread se update karo
        Clock.schedule_once(
            lambda dt: self.show_reply(reply)
        )

    def show_reply(self, reply):

        self.chat.text += (
            f"\n\nChitragupt: {reply}"
        )


Chitragupt().run()
