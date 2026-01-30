

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

    @classmethod
    def reset_instance(mcs, cls):
        """
        Reset the singleton instance for a specific class.
        
        This is intended for testing purposes to ensure proper isolation
        between tests. In production code, singletons persist for the 
        application lifetime.
        
        :param cls: The class whose singleton instance should be reset
        """
        if cls in mcs._instances:
            del mcs._instances[cls]

    @classmethod
    def reset_all_instances(mcs):
        """
        Reset all singleton instances.
        
        This is intended for testing purposes to ensure proper isolation
        between tests. Use with caution as it clears all singleton caches.
        """
        mcs._instances.clear()
