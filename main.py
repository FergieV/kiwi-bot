import asyncio
import sys
from PyQt5.QtWidgets import QApplication
import qasync
from kiwibot.connection import BotManager
from kiwibot.ui import MainWindow

def main():
    # Create QApplication first
    app = QApplication(sys.argv)
    
    # Create event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    async def init():
        # Initialize bot manager
        bot_manager = BotManager()
        await bot_manager.load_configs()
        
        # Create and show window
        window = MainWindow(bot_manager)
        window.show()
        
        # Start all bots
        await bot_manager.start_all()
        
        return window, bot_manager

    # Setup cleanup
    async def cleanup():
        window, bot_manager = loop.result
        await bot_manager.stop_all()
        app.quit()

    # Store cleanup
    app.cleanup = cleanup

    # Run initialization
    loop.result = loop.run_until_complete(init())
    
    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        loop.create_task(app.cleanup())
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start event loop
    return loop.run_forever()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass 