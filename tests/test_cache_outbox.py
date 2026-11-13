import os
import threading
import unittest
from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
from sqlalchemy.orm.attributes import flag_modified
from medsenger_api.cache_updates import CacheUpdateOutbox


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = 'cache_test_item'
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int]
    label: Mapped[str]
    last_run: Mapped[int] = mapped_column(default=0)
    settings: Mapped[dict] = mapped_column(sa.JSON, default=dict)


class CacheOutboxTest(unittest.TestCase):
    url = 'sqlite://'

    def setUp(self):
        self.engine = sa.create_engine(self.url)
        self.sent = []
        self.active = True
        self.outbox = CacheUpdateOutbox(
            Base.metadata,
            lambda: self.engine,
            'test',
            self.send,
            lambda conn, cid: self.active,
            window=0,
        )
        self.outbox.watch(
            Item,
            lambda row: (
                row['contract_id'],
                (row['id'], row['label'], row['settings']),
            ),
        )
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.outbox.install()
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        self.outbox.uninstall()
        self.engine.dispose()

    def send(self, cid):
        self.sent.append(cid)
        return 'ok'

    def add(self, count=1, contract=1):
        self.session.add_all(
            [Item(contract_id=contract, label=str(i)) for i in range(count)]
        )
        self.session.commit()

    def row(self):
        with self.engine.connect() as conn:
            return conn.execute(sa.select(self.outbox.table)).mappings().first()

    def test_many_objects_and_intermediate_commits_make_one_delivery(self):
        with self.outbox.batch():
            self.add(5)
            self.add(5)
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.sent, [1])
        self.assertEqual(self.outbox.drain(), 0)

    def test_identical_save_and_runtime_updates_do_not_invalidate(self):
        self.add()
        self.outbox.drain()
        item = self.session.query(Item).first()
        item.label = item.label
        item.last_run = 10
        self.session.commit()
        self.assertEqual(self.outbox.drain(), 0)
        self.assertEqual(self.sent, [1])
        item.label = 'changed'
        self.session.commit()
        self.assertEqual(self.outbox.drain(), 1)

    def test_rollback_discards_invalidation(self):
        self.session.add(Item(contract_id=1, label='rolled back'))
        self.session.flush()
        self.session.rollback()
        self.assertIsNone(self.row())
        self.assertEqual(self.outbox.drain(), 0)

    def test_another_app_adapter_cannot_overwrite_pending_flush_state(self):
        other = CacheUpdateOutbox(
            sa.MetaData(),
            lambda: self.engine,
            'test',
            lambda cid: self.fail('Unrelated adapter sent a notification'),
            lambda conn, cid: True,
        )
        other.install()
        try:
            self.add()
            self.assertEqual(self.outbox.drain(), 1)
            self.assertEqual(self.sent, [1])
        finally:
            other.uninstall()

    def test_scalar_types_are_distinct_and_object_key_order_is_not(self):
        self.add()
        self.outbox.drain()
        item = self.session.query(Item).first()
        for value in (False, 0, 0.0, '0', None):
            item.settings = {'value': value, 'name': 'Limit'}
            flag_modified(item, 'settings')
            self.session.commit()
            self.assertEqual(self.outbox.drain(), 1)
        item.settings = {'name': 'Limit', 'value': None}
        self.session.commit()
        self.assertEqual(self.outbox.drain(), 0)

    def test_failure_after_partial_commits_keeps_committed_changes(self):
        with self.assertRaises(RuntimeError):
            with self.outbox.batch():
                self.add()
                self.session.add(Item(contract_id=2, label='not committed'))
                self.session.flush()
                self.session.rollback()
                raise RuntimeError('interrupted')
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.sent, [1])

    def test_bulk_deletion_and_edit_are_tracked_by_actual_contract(self):
        self.add(contract=1)
        self.add(contract=2)
        self.outbox.drain()
        self.sent.clear()
        self.session.query(Item).filter_by(contract_id=1).delete(
            synchronize_session=False
        )
        self.session.query(Item).filter_by(contract_id=2).update(
            {'label': 'edited'}, synchronize_session=False
        )
        self.session.commit()
        self.outbox.drain()
        self.assertEqual(sorted(self.sent), [1, 2])

    def test_bulk_runtime_update_and_rollback_do_not_create_work(self):
        self.add()
        self.outbox.drain()
        self.session.query(Item).update({'last_run': 20})
        self.session.commit()
        self.assertEqual(self.outbox.drain(), 0)
        self.session.query(Item).delete()
        self.session.rollback()
        self.assertEqual(self.outbox.drain(), 0)

    def test_delivery_failure_survives_and_can_retry(self):
        self.add()
        self.outbox.send = lambda cid: None
        self.assertEqual(self.outbox.drain(), 0)
        self.assertEqual(self.row()['delivered'], 0)
        with self.engine.begin() as conn:
            conn.execute(self.outbox.table.update().values(due_at=datetime.utcnow()))
        self.outbox.send = self.send
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.row()['last_error'], None)

    def test_removed_contract_is_acknowledged_without_calling_backend(self):
        self.add()
        self.active = False
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.sent, [])

    def test_new_change_during_delivery_is_not_acknowledged_as_old_work(self):
        self.add()

        def send(cid):
            self.outbox.send = self.send
            with Session(self.engine) as other:
                other.add(Item(contract_id=1, label='new'))
                other.commit()
            return 'ok'

        self.outbox.send = send
        self.assertEqual(self.outbox.drain(), 1)
        self.assertGreater(self.row()['requested'], self.row()['delivered'])
        self.assertEqual(self.outbox.drain(), 1)


@unittest.skipUnless(os.getenv('TEST_POSTGRES_URL'), 'isolated PostgreSQL required')
class PostgreSQLCacheOutboxTest(CacheOutboxTest):
    url = os.getenv('TEST_POSTGRES_URL', 'sqlite://')

    def test_new_change_during_delivery_is_not_acknowledged_as_old_work(self):
        # Writers wait for the publisher's session lock. They create a new
        # revision after it releases, without depending on Celery delivery order.
        self.add()
        started, finished = threading.Event(), threading.Event()
        errors = []

        def writer():
            try:
                with Session(self.engine) as other:
                    started.set()
                    other.add(Item(contract_id=1, label='new'))
                    other.commit()
                finished.set()
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=writer)

        def send(cid):
            thread.start()
            self.assertTrue(started.wait(2))
            self.assertFalse(finished.wait(0.1))
            return 'ok'

        self.outbox.send = send
        self.outbox.drain()
        thread.join(3)
        self.assertEqual(errors, [])
        self.assertTrue(finished.is_set())
        self.outbox.send = self.send
        self.assertEqual(self.outbox.drain(), 1)

    def test_batch_cannot_publish_between_commits_and_does_not_block_other_contracts(
        self,
    ):
        self.add(contract=2)
        with self.outbox.batch():
            self.add(contract=1)
            self.assertEqual(self.outbox.drain(), 1)
            self.assertEqual(self.sent, [2])
            self.add(contract=1)
            self.assertEqual(self.outbox.drain(), 0)
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.sent, [2, 1])

    def test_two_publishers_send_once(self):
        self.add()
        started, finish = threading.Event(), threading.Event()
        errors = []

        def send(cid):
            self.sent.append(cid)
            started.set()
            finish.wait(3)
            return 'ok'

        self.outbox.send = send

        def worker():
            try:
                self.outbox.drain()
            except Exception as error:
                errors.append(error)
                started.set()

        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(started.wait(3))
            self.assertEqual(self.outbox.drain(), 0)
        finally:
            finish.set()
            thread.join(3)
        self.assertEqual(errors, [])
        self.assertEqual(self.sent, [1])

    def test_runtime_only_batch_does_not_block_pending_delivery(self):
        self.add()
        with self.outbox.batch():
            item = self.session.query(Item).first()
            item.last_run = 42
            self.session.commit()
            self.assertEqual(self.outbox.drain(), 1)

    def test_dead_batch_connection_releases_lock_and_preserves_committed_work(self):
        with self.assertRaises(sa.exc.DBAPIError):
            with self.outbox.batch():
                self.add()
                held, _ = next(iter(self.outbox._batch.get().values()))
                pid = held.execute(sa.text('select pg_backend_pid()')).scalar()
                held.commit()
                with self.engine.begin() as killer:
                    killer.execute(
                        sa.text('select pg_terminate_backend(:pid)'), {'pid': pid}
                    )
        self.assertEqual(self.outbox.drain(), 1)
        self.assertEqual(self.sent, [1])
