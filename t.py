from myapp.models import Transaction,User
def insert_txns():
    items = []
    for i in range(1_000_000):
        if i%500_000 == 0:
            Transaction.objects.bulk_create(items)
            print(i)
            items.clear()
        items.append(Transaction(sender_id=1, receiver_id=2, amount=1, description=f'txn {i+1}'))
    Transaction.objects.bulk_create(items)

def insert_users():
    items = []
    for i in range(10_000_000):
        if i%500_000 == 0:
            User.objects.bulk_create(items)
            print(i)
            items.clear()
        p="pbkdf2_sha256$1200000$mCDcZ45pvfMGheNsMBJPX0$V0P3KXN8RMploCGRm2/ct7WROYyiPU/VMUic9kx3mOc="
        items.append(User(password=p, username=f'u{i}',first_name=f'n{i}'))
    User.objects.bulk_create(items)

insert_users()