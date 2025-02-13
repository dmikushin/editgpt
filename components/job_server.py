from gi.repository import GLib
import asyncio
import threading
import weakref

class EditGPTJobData:
    def __init__(self, document, start_iter, end_iter):
        self.document = document
        self.start_iter = start_iter
        self.end_iter = end_iter
        self.lock = threading.Lock()
        self.queue = []
        self.state = 'begin'

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

    async def generate_text_async(self, prompt, document, start_iter, end_iter):
        try:
            start_offset = start_iter.get_offset()
            data = EditGPTJobData(document, start_iter, end_iter)
            self.idle_handler = GLib.idle_add(self.process_text_queue, data)

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

            input = document.get_text(start_iter, end_iter, True)

            process.stdin.write(input.encode())
            await process.stdin.drain()
            process.stdin.close()

            async def read_stream(stream, callback):
                while True:
                    line = await stream.read(1)
                    if line:
                        callback(line.decode())
                    else:
                        break

            def handle_stdout(token):
                nonlocal start_offset
                with data.lock:
                    data.queue.append((start_offset, token))
                start_offset += len(token)
            def handle_stderr(token):
                print(token)

            await asyncio.gather(
                read_stream(process.stdout, handle_stdout),
                read_stream(process.stderr, handle_stderr))

            with data.lock:
                data.state = 'end'
            
        except Exception as e:
            print(f"Failed to execute prompt: {e}")
        
    def process_text_queue(self, data):
        with data.lock:
            if data.state == 'begin':
                data.document.begin_user_action()
                data.document.delete(data.start_iter, data.end_iter)
                data.state = 'inprogress'
                # Continue calling this function.
                return True
            elif data.state == 'inprogress':
                while data.queue:
                    start_offset, token = data.queue.pop(0)
                    start_iter = data.document.get_iter_at_offset(start_offset)
                    data.document.insert(start_iter, token)
                # Continue calling this function.
                return True
            elif data.state == 'end':
                data.document.end_user_action()
                # Remove the function from the list of event sources
                # and will not be called again.
                return False

    def dispatch_async_task(self, prompt, document, start_iter, end_iter):
        asyncio.run_coroutine_threadsafe(
            self.generate_text_async(prompt, document, start_iter, end_iter),
            self.loop)
