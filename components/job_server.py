from gi.repository import GLib
import asyncio
import threading
import weakref

class EditGPTJobServer:
    _instance = None

    def __init__(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        if not self.loop.is_running():
            threading.Thread(target=self.start_event_loop, args=(self.loop,), daemon=True).start()

    def start_event_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def generate_text_async(self, prompt, input, document, start_offset):
        try:
            document_ref = weakref.ref(document)
            
            # Begin user action to group all insertions into one undo step
            document.begin_user_action()
            
            cmd = ['sgpt', '--no-md']
            if 'generate_only_code' in prompt and prompt['generate_only_code']:
                cmd.append('--code')
            cmd.append(prompt["text"])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send the input string to the process
            process.stdin.write(input.encode())
            await process.stdin.drain()
            process.stdin.close()

            async def read_stream(stream, callback):
                while True:
                    line = await stream.read(1)  # Read one byte at a time
                    if line:
                        callback(line.decode())
                    else:
                        break

            def handle_stdout(token):
                nonlocal start_offset
                if document_ref() is not None:
                    GLib.idle_add(self.insert_text, document, start_offset, token)
                    start_offset += len(token)

            def handle_stderr(token):
                print(token)

            # Read stdout and stderr concurrently
            await asyncio.gather(
                read_stream(process.stdout, handle_stdout),
                read_stream(process.stderr, handle_stderr))
            
        except Exception as e:
            print(f"Failed to execute prompt: {e}")
        
        finally:
            # End user action after all insertions are done
            if document_ref() is not None:
                document.end_user_action()

    def insert_text(self, document, start_offset, token):
        document.begin_user_action()
        start_iter = document.get_iter_at_offset(start_offset)
        document.insert(start_iter, token)
        document.end_user_action()
        return False  # Stop the idle function

    def dispatch_async_task(self, prompt, input, document, start_offset):
        # Schedule the coroutine to run in the background
        asyncio.run_coroutine_threadsafe(
            self.generate_text_async(prompt, input, document, start_offset),
            self.loop)
