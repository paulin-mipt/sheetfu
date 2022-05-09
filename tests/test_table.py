import datetime

import pytest

from sheetfu import SpreadsheetApp, Table
from sheetfu.model import Range
from sheetfu.modules.table import Item
from tests.utils import mock_google_sheets_responses


class TestTableRanges:

    def test_full_range_data(self, full_table):
        for item in full_table.items:
            assert item.backgrounds is not None
            assert item.notes is not None
            assert item.font_colors is not None
            assert item.values is not None
            assert len(item.header) == len(full_table.header)

    def test_items(self, full_table):
        assert full_table.items is not None
        assert type(full_table.items) == list
        assert len(full_table.items) == full_table.full_range.coordinates.number_of_rows - 1

    def test_items_instance(self, full_table):
        for item in full_table.items:
            assert isinstance(item, Item)
            assert isinstance(item.get_range(), Range)

    def test_table_length(self, full_table):
        assert len(full_table) == len(full_table.items)

    def test_for_loops(self, full_table):
        for item in full_table:
            assert isinstance(item, Item)


class TestItem:
    http_mocks = mock_google_sheets_responses([
        'discovery.json',
        'discovery.json',
        'discovery.json',
        'table_get_sheets.json',
        'discovery.json',
        'table_check_data_range.json',
        'discovery.json',
        'table_values.json',
        'discovery.json',
        'table_values.json',
        'discovery.json',
        'table_notes.json',
        'discovery.json',
        'table_backgrounds.json',
        'discovery.json',
        'table_font_colors.json'
    ])
    sa = SpreadsheetApp(http=http_mocks)
    table_range = sa.open_by_id('whatever').get_sheet_by_name('Sheet1').get_data_range()
    table = Table(
        full_range=table_range,
        notes=True,
        backgrounds=True,
        font_colors=True
    )
    item = Item(
        parent_table=table,
        row_index=0,
        header=['name', 'surname'],
        values=['john', 'doe'],
        notes=['note name', 'note surname'],
        backgrounds=['#ffffff', '#fff000'],
        font_colors=['#000fff', '#000000']
    )

    def test_get_field_value(self):
        assert self.item.get_field_value('name') == 'john'
        assert self.item.get_field_value('surname') == 'doe'

    def test_get_field_note(self):
        assert self.item.get_field_note('name') == 'note name'
        assert self.item.get_field_note('surname') == 'note surname'

    def test_get_field_background(self):
        assert self.item.get_field_background('name') == '#ffffff'
        assert self.item.get_field_background('surname') == '#fff000'

    def test_get_field_font_colors(self):
        assert self.item.get_field_font_color('name') == '#000fff'
        assert self.item.get_field_font_color('surname') == '#000000'

    def test_convert_to_dict(self):
        assert self.item.to_dict() == {
            "name": "john",
            "surname": "doe"
        }


class TestTableItemRanges:

    def test_table_range(self, full_table):
        assert full_table.full_range.a1 == 'Sheet1!A1:C6'

    def test_table_items_range(self, full_table):
        assert full_table.items_range.a1 == 'Sheet1!A2:C6'

    def test_first_item_range(self, full_table):
        first_item = full_table[0]
        assert isinstance(first_item, Item)
        assert first_item.get_range().a1 == 'Sheet1!A2:C2'

    def test_field_ranges_type(self, full_table):
        second_item = full_table[1]
        assert isinstance(second_item, Item)
        assert second_item.get_range().a1 == 'Sheet1!A3:C3'

        for field in ['name', 'surname', 'age']:
            field_range = second_item.get_field_range(field)
            assert isinstance(field_range, Range)

    def test_field_ranges(self, full_table):
        third_item = full_table[2]
        assert third_item.get_field_range('name').a1 == 'Sheet1!A4'
        assert third_item.get_field_range('surname').a1 == 'Sheet1!B4'
        assert third_item.get_field_range('age').a1 == 'Sheet1!C4'


class TestTableCRUD:
    def test_add_one_item(self, table):
        assert table.full_range.a1 == "Sheet1!A1:C6"
        assert table.items_range.a1 == "Sheet1!A2:C6"
        assert len(table.items) == 5
        table.add_one({"name": "Alex", "surname": "Muelas", "age": 1})
        assert table.full_range.a1 == "Sheet1!A1:C7"
        assert table.items_range.a1 == "Sheet1!A2:C7"
        assert len(table.batches) == 1
        assert len(table.items) == 6
        table.commit()
        assert len(table.batches) == 0
        assert len(table.items) == 6

    def test_add_several_items(self, table):
        assert len(table.items) == 5
        assert table.full_range.a1 == "Sheet1!A1:C6"
        assert table.items_range.a1 == "Sheet1!A2:C6"
        table.add_one({"name": "John", "surname": "Snow", "age": 2})
        table.add_one({"name": "Ned", "surname": "Stark", "age": 3})
        table.add_one({"name": "Tyrion", "surname": "Lannister", "age": 4})
        assert len(table.batches) == 3
        assert len(table.items) == 8
        table.commit()
        assert len(table.batches) == 0
        assert len(table.items) == 8
        assert table.full_range.a1 == "Sheet1!A1:C9"
        assert table.items_range.a1 == "Sheet1!A2:C9"

    def test_sort_table(self, table):
        assert len(table.items) == 5
        table.sort("name")
        assert len(table.items) == 5
        assert len(table.batches) == 1
        assert table.items[0].get_field_value("name") == "jane"
        assert table.items[0].row_index == 0
        assert table.items[4].get_field_value("name") == "random"
        table.sort("name", reverse=True)
        assert table.items[0].get_field_value("name") == "random"
        assert table.items[0].row_index == 0
        assert table.items[4].get_field_value("name") == "jane"
        assert table.items[4].row_index == 4
        for index, item in enumerate(table.items):
            assert item.row_index == index

    def test_generate_set_own_range_values_batches(self, table):
        empty_values = [["value", "value", "value"]] * 5
        table._generate_set_own_range_values_batches(range=table.items_range, values=empty_values)
        assert len(table.batches) == 1
        assert type(table.batches[0]) == dict
        assert table.batches[0]["updateCells"]["range"]["startRowIndex"] == 1
        assert table.batches[0]["updateCells"]["range"]["endRowIndex"] == 6
        assert table.batches[0]["updateCells"]["range"]["startColumnIndex"] == 0
        assert table.batches[0]["updateCells"]["range"]["endColumnIndex"] == 3
        assert len(table.batches[0]["updateCells"]["rows"]) == 5
        for row in table.batches[0]["updateCells"]["rows"]:
            for value in row["values"]:
                assert value["userEnteredValue"]["stringValue"] == "value"

    def test_delete_all(self, table):
        table.delete_all()
        assert table.items_range is None
        assert table.full_range.a1 == "Sheet1!A1:C1"
        assert len(table.items) == 0
        assert len(table.batches) == 1
        assert table.batches[0]["updateCells"]["range"]["startRowIndex"] == 1
        assert table.batches[0]["updateCells"]["range"]["endRowIndex"] == 6
        assert table.batches[0]["updateCells"]["range"]["startColumnIndex"] == 0
        assert table.batches[0]["updateCells"]["range"]["endColumnIndex"] == 3
        assert len(table.batches[0]["updateCells"]["rows"]) == 5
        for row in table.batches[0]["updateCells"]["rows"]:
            for value in row["values"]:
                assert value["userEnteredValue"]["stringValue"] == ""

    def test_delete_and_add(self, table):
        table.add_one({"name": "John", "surname": "Snpw", "age": 2})
        assert len(table.items) == 6
        table.delete_all()
        assert table.items_range is None
        assert table.full_range.a1 == "Sheet1!A1:C1"
        assert len(table.items) == 0
        assert len(table.batches) == 2
        table.add_one({"name": "Peter", "surname": "Mike", "age": 15})
        table.add_one({"name": "Ned", "surname": "Stark", "age": 3})
        assert len(table.items) == 2
        assert len(table.batches) == 4
        assert table.items_range.a1 == "Sheet1!A2:C3"
        assert table.full_range.a1 == "Sheet1!A1:C3"

    def test_sort_and_delete(self, table):
        table.add_one({"name": "John", "surname": "Snow", "age": 2})
        table.sort("age")
        assert len(table.items) == 6
        assert len(table.batches) == 2
        table.delete_all()
        table.sort("name")
        assert len(table.items) == 0
        assert len(table.batches) == 3
        table.add_one({"name": "John", "surname": "Snow", "age": 2})
        table.sort("name")
        assert len(table.items) == 1
        assert len(table.batches) == 5
        assert table.items_range.a1 == "Sheet1!A2:C2"
        assert table.full_range.a1 == "Sheet1!A1:C2"

    def test_delete_indexes(self, table):
        assert table.items[0].get_field_value("name") == "philippe"
        table.add_one({"name": "John", "surname": "Snow", "age": 2})
        assert len(table.items) == 6
        table.delete([0, 5])
        assert len(table.items) == 4
        assert table.items[0].get_field_value("name") == "john"
        assert table.items[3].get_field_value("name") == "random"

    def test_delete_items(self, table):
        assert table.items[0].get_field_value("name") == "philippe"
        table.add_one({"name": "Jake", "surname": "Lannister", "age": 15})
        new_item_2 = table.add_one({"name": "John", "surname": "Snow", "age": 2})
        assert len(table.items) == 7
        table.delete_items([new_item_2, table.items[1]])
        assert len(table.items) == 5
        assert table.items[0].get_field_value("name") == "philippe"
        assert table.items[4].get_field_value("name") == "Jake"

    def test_delete_mixed(self, table):
        assert len(table.items) == 5
        table.delete_items(table.items[0])
        table.delete([1, 3])
        assert len(table.items) == 2
        assert table.items[0].get_field_value("name") == "john"
        assert table.items[1].get_field_value("name") == "mike"

    def test_delete_duplicate(self, table):
        new_item = table.add_one({"name": "Jake", "surname": "Lannister", "age": 15})
        table.delete_items([new_item])
        with pytest.raises(ValueError):
            table.delete_items([new_item])

    def test_error_deletes(self, table):
        with pytest.raises(ValueError):
            table.delete(5)

        with pytest.raises(ValueError):
            table.delete_items(0)

        assert len(table.items) == 5
        table.delete([0, 2])
        assert len(table.items) == 3
        with pytest.raises(ValueError):
            table.delete([3])

    def get_table_from_sheet(self, spreadsheet):
        table = Table.get_table_from_sheet(spreadsheet, "Sheet1")
        assert len(table.items) == 5


class TestTableSelector:

    def test_or_clause(self, table):
        values = table.select([[{"name": "jane"}, {"name": "john"}]])
        assert len(values) == 2

    def test_and_clause(self, table):
        values = table.select([{"age": 25}, [{"name": "john"}]])
        assert len(values) == 1
        values = table.select([{"name": 'philippe'}, {"surname": 'oger'}])
        assert len(values) == 1
        values = table.select({"name": 'jane', "age": 25})
        assert len(values) == 1

    def test_empty_select(self, table):
        values = table.select([{"age": 25}, [{"name": "phillipe"}]])
        assert len(values) == 0

    def test_value_error_exception(self, table):
        with pytest.raises(ValueError):
            table.select([[25, 35]])


class TestTableDatetimeField:
    http_mocks = mock_google_sheets_responses([
        'table_get_sheets.json',
        'table_values_datetime.json',
        'table_values_datetime.json'
    ])
    sa = SpreadsheetApp(http=http_mocks)
    sheet = sa.open_by_id('whatever').get_sheet_by_name('Sheet1')
    data_range = sheet.get_range_from_a1("A1:B3")
    table = Table(
        full_range=data_range
    )

    def test_table_size(self):
        assert len(self.table) == 2
        assert len(self.table.header) == 2

    def test_first_row(self):
        row = self.table[0]
        birthday = row.get_field_value("birthday")
        assert row.get_field_value("name") == "foo"
        assert isinstance(birthday, datetime.datetime)
        assert birthday.year == 2021
        assert birthday.month == 5
        assert birthday.day == 1

    def test_second_row(self):
        row = self.table[1]
        birthday = row.get_field_value("birthday")
        assert row.get_field_value("name") == "bar"
        assert isinstance(birthday, datetime.datetime)
        assert birthday.year == 2021
        assert birthday.month == 9
        assert birthday.day == 30

    def test_set_datetime_values(self):
        for row in self.table:
            birthday = row.get_field_value("birthday")
            new_birthday = birthday + datetime.timedelta(days=1)
            row.set_field_value("birthday", new_birthday)

        # we then check the request put in the batch
        first_request = self.table.batches[0]
        first_value = first_request["updateCells"]["rows"][0]["values"][0]["userEnteredValue"]["numberValue"]
        assert first_value == 44318.0

        second_request = self.table.batches[1]
        second_value = second_request["updateCells"]["rows"][0]["values"][0]["userEnteredValue"]["numberValue"]
        assert second_value == 44470.0

        for batch in self.table.batches:
            assert batch["updateCells"]["rows"][0]["values"][0]["userEnteredFormat"]["numberFormat"]["type"] == "DATE_TIME"
