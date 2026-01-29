"""Utility module providing event queues and JS style async awaiter promises"""

import queue

class Event:
    """
    Event sender that can push event notifications to consumers.
    """

    def __init__(self):
        self.__senders = []
        self.__chain = []

    def bind(self, consumer : "EventConsumer", event_id = None):
        """
        Bind a consumer to this event.
        
        :param consumer: Consumer to bind
        :type consumer: "EventConsumer"
        """

        sender = consumer.create_sender(event_id)
        self.__senders.append(sender)

        return sender.get_event()
    
    def chain(self, other_event : "Event"):
        """
        Chain this event to another event, so that when this event is called,
        the other event is also called.
        
        :param other_event: Event to chain to
        :type other_event: "Event"
        """

        self.__chain.append(other_event)

    def unbind(self, consumer : "EventConsumer"):
        """
        Unbind a consumer to this event.
        
        :param consumer: Consumer to unbind
        :type consumer: "EventConsumer"
        """

        for sender in self.__senders:
            if sender.get_consumer() == consumer:
                self.__senders.remove(sender)
                break

    def call(self):
        """
        Send this event to all bound event consumer queues.
        """

        for sender in self.__senders:
            sender.send()

        for chained_event in self.__chain:
            chained_event.call()

class EventConsumer:
    """
    Event subscriber that can pull events from senders
    """
    def __init__(self):
        self.__queue = queue.Queue()

        self.__next_event = 0

    def send(self, event, block = True, timeout = None):
        """
        Send an event to this consumer queue.
        
        :param event: Event ID
        :param block: Should block if event queue is full?
        :param timeout: Timeout to wait if event queue is full
        """

        self.__queue.put(event, block=block, timeout=timeout)

    def get(self, block = True, timeout = 1):
        """
        Wait for an event to be enqueued to this event queue.
        
        :param block: Should block if event queue is empty?
        :param timeout: Timeout to wait if event queue is empty
        """

        e = None

        try:
            e = self.__queue.get(block=block, timeout=timeout)
        except queue.Empty:
            pass

        return e


    def create_sender(self, event_id = None):
        """
        Construct a sender object for this queue.
        """

        if event_id is None:
            event_id = self.__next_event
            self.__next_event+=1

        return self._EventSender(self, event_id)

    class _EventSender:
        def __init__(self, flag : "EventConsumer", event: int):
            self.__flag = flag
            self.__event = event

        def send(self, block = True, timeout = None):
            """
            Send an event to the queue this sender is bound to.
            
            :param block: Should block if event queue is full?
            :param timeout: Timeout to wait if event queue is full
            """
            self.__flag.send(self.__event, block, timeout)

        def get_consumer(self):
            """
            Get the event consumer queue this sender is bound to.
            """

            return self.__flag

        def get_event(self):
            """
            Get event ID this sender is configured to send.
            """

            return self.__event

class Awaiter:
    """
    JS-style promise-like awaiter object.
    """

    class _AwaiterHandle:
        def __init__(self, awaiter : "Awaiter"):
            self.__awaiter = awaiter

        def then(self, fn, pargs: list | None = None, kwargs: dict | None = None):
            """
            Do if awaited operation finishes successfully.
            
            :param fn: Function to call
            :param pargs: pargs to pass in to fn as additional args if desired
            :type pargs: list | None
            :param kwargs: kwargs to pass in to fn as additional args if desired
            :type kwargs: dict | None
            """

            if pargs is None:
                pargs = []

            if kwargs is None:
                kwargs = dict()

            return self.__awaiter.then(fn, pargs, kwargs)

        def catch(self, fn, pargs: list | None = None, kwargs: dict | None = None):
            """
            Do if awaited operation has an abnormal result.
            
            :param fn: Function to call
            :param pargs: pargs to pass in to fn as additional args if desired
            :type pargs: list | None
            :param kwargs: kwargs to pass in to fn as additional args if desired
            :type kwargs: dict | None
            """

            if pargs is None:
                pargs = []

            if kwargs is None:
                kwargs = dict()

            return self.__awaiter.catch(fn, pargs, kwargs)

    def __init__(self):
        self.__params = dict()
        self.__cb_fn = None
        self.__except_fn = None

        self.__cb_pargs = None
        self.__cb_kwargs = None

        self.__except_pargs = None
        self.__except_kwargs = None

    def get_handle(self):
        """
        Construct an awaiter handle for this awaiter.
        """

        return self._AwaiterHandle(self)

    def add_param(self, kw, value):
        """
        Add kwarg to pass to awaiter handles

        :param kw: Parameter keyword
        :param value: Parameter value
        """

        self.__params[kw] = value

    def then(self, fn, pargs: list | None = None, kwargs: dict | None = None):
        """
        Do if awaited operation finishes successfully.
        
        :param fn: Function to call
        :param pargs: pargs to pass in to fn as additional args if desired
        :type pargs: list | None
        :param kwargs: kwargs to pass in to fn as additional args if desired
        :type kwargs: dict | None
        """

        if pargs is None:
            pargs = []
        if kwargs is None:
            kwargs = dict()

        self.__cb_fn = fn
        self.__cb_pargs = list(pargs)
        self.__cb_kwargs = dict(kwargs)

        return self._AwaiterHandle(self)

    def catch(self, fn, pargs: list | None = None, kwargs: dict | None = None):
        """
        Do if awaited operation has an abnormal result.
        
        :param fn: Function to call
        :param pargs: pargs to pass in to fn as additional args if desired
        :type pargs: list | None
        :param kwargs: kwargs to pass in to fn as additional args if desired
        :type kwargs: dict | None
        """

        if pargs is None:
            pargs = []
        if kwargs is None:
            kwargs = dict()

        self.__except_fn = fn
        self.__except_pargs = list(pargs)
        self.__except_kwargs = dict(kwargs)

        return self._AwaiterHandle(self)

    def call(self, *pargs, **kwargs):
        """
        Call the awaiting function.
        """
        if self.__cb_fn is not None:
            combined_args = self.__cb_kwargs

            for key in self.__params.keys():
                combined_args[key] = self.__params[key]

            for key in kwargs.keys():
                combined_args[key] = kwargs[key]

            self.__cb_fn(*(list(pargs) + self.__cb_pargs), **combined_args)

    def throw(self, *pargs, **kwargs):
        """
        Call the awaiting non-normal function.
        """

        if self.__except_fn is not None:
            combined_args = self.__except_kwargs

            for key in self.__params.keys():
                combined_args[key] = self.__params[key]

            for key in kwargs.keys():
                combined_args[key] = kwargs[key]

            self.__except_fn(*(list(pargs) + self.__except_pargs), **combined_args)
