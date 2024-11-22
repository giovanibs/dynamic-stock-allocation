from dataclasses import dataclass


@dataclass
class RedisChannels:
    CREATE_BATCH            : str = 'create_batch'
    ALLOCATE_LINE           : str = 'allocate_line'
    DEALLOCATE_LINE         : str = 'deallocate_line'
    CHANGE_BATCH_QUANTITY   : str = 'change_batch_quantity'
    BATCH_CREATED           : str = 'batch_created'
    BATCH_QUANTITY_CHANGED  : str = 'batch_quantity_changed'
    LINE_ALLOCATED          : str = 'line_allocated'
    LINE_DEALLOCATED        : str = 'line_deallocated'
    OUT_OF_STOCK            : str = 'out_of_stock'
    CONSUMER_PING           : str = 'consumer_ping'
    CONSUMER_PONG           : str = 'consumer_pong'
