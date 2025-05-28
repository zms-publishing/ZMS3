import ZODB, ZODB.FileStorage

storage = ZODB.FileStorage.FileStorage("/home/zope/instance/var/Data.fs")
db = ZODB.DB(storage)
connection = db.open()
root = connection.root()

# Initialize root object if needed
if not hasattr(root, 'app_root'):
    from persistent.mapping import PersistentMapping
    root['app_root'] = PersistentMapping()
    import transaction
    transaction.commit()

connection.close()
db.close()
print("New Data.fs-file created successfully!")
