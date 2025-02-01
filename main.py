import asyncio
import sys
from PyQt5.QtWidgets import QApplication
import qasync
from kiwibot.connection import BotManager
from kiwibot.ui import MainWindow

async def main():
    bot_manager = BotManager()
    await bot_manager.load_configs()
    
    app = QApplication(sys.argv)
    window = MainWindow(bot_manager)
    window.show()
    
    # Start all bots
    await bot_manager.start_all()
    
    # Setup cleanup
    async def cleanup():
        await bot_manager.stop_all()
        app.quit()
    
    return app, cleanup

if __name__ == '__main__':
    try:
        loop = qasync.QEventLoop(sys.argv)
        asyncio.set_event_loop(loop)
        app, cleanup = loop.run_until_complete(main())
        
        # Handle shutdown gracefully
        def signal_handler(signum, frame):
            loop.create_task(cleanup())
        
        import signal
        signal.signal(signal.SIGINT, signal_handler)
        
        loop.run_forever()
    except KeyboardInterrupt:
        pass 