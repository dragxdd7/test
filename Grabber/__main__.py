import importlib
from Grabber import Grabberu, LOGGER, application
from Grabber.modules import ALL_MODULES

# Import all modules dynamically
for module_name in ALL_MODULES:
    importlib.import_module("Grabber.modules." + module_name)

def main() -> None:
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    Grabberu.start()
    LOGGER.info("Bot started")
    main()