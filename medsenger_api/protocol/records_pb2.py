# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protocol/records.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x16protocol/records.proto\x12\x07records\"\x07\n\x05\x45mpty\"\x12\n\x04User\x12\n\n\x02id\x18\x01 \x01(\x05\"\x1b\n\rRecordRequest\x12\n\n\x02id\x18\x01 \x01(\x03\"5\n\x0c\x43\x61tegoryList\x12%\n\ncategories\x18\x01 \x03(\x0b\x32\x11.records.Category\"\xfe\x02\n\x08\x43\x61tegory\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x18\n\x0b\x64\x65scription\x18\x03 \x01(\tH\x00\x88\x01\x01\x12\x11\n\x04unit\x18\x04 \x01(\tH\x01\x88\x01\x01\x12\x11\n\x04type\x18\x05 \x01(\tH\x02\x88\x01\x01\x12#\n\x16\x64\x65\x66\x61ult_representation\x18\x06 \x01(\tH\x03\x88\x01\x01\x12\x16\n\tis_legacy\x18\x07 \x01(\x08H\x04\x88\x01\x01\x12\x18\n\x0bsubcategory\x18\x08 \x01(\tH\x05\x88\x01\x01\x12\x1b\n\x0e\x64octor_can_add\x18\t \x01(\x08H\x06\x88\x01\x01\x12\x1f\n\x12\x64octor_can_replace\x18\n \x01(\x08H\x07\x88\x01\x01\x42\x0e\n\x0c_descriptionB\x07\n\x05_unitB\x07\n\x05_typeB\x19\n\x17_default_representationB\x0c\n\n_is_legacyB\x0e\n\x0c_subcategoryB\x11\n\x0f_doctor_can_addB\x15\n\x13_doctor_can_replace\"=\n\nRecordList\x12 \n\x07records\x18\x01 \x03(\x0b\x32\x0f.records.Record\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\"4\n\x0cRecordSource\x12\x0f\n\x02id\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x0c\n\x04name\x18\x02 \x01(\tB\x05\n\x03_id\"4\n\nRecordFile\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\"\x87\x02\n\x06Record\x12\n\n\x02id\x18\x01 \x01(\x03\x12\r\n\x05value\x18\x02 \x01(\t\x12\x13\n\x0b\x63\x61tegory_id\x18\x03 \x01(\x03\x12\x0f\n\x07user_id\x18\x04 \x01(\x05\x12\x12\n\ncreated_at\x18\x05 \x01(\x03\x12\x12\n\nupdated_at\x18\x06 \x01(\x03\x12\x0e\n\x06params\x18\x07 \x01(\t\x12\x11\n\tadditions\x18\x08 \x01(\t\x12\r\n\x05group\x18\t \x01(\t\x12*\n\x06source\x18\n \x01(\x0b\x32\x15.records.RecordSourceH\x00\x88\x01\x01\x12+\n\x0e\x61ttached_files\x18\x0b \x03(\x0b\x32\x13.records.RecordFileB\t\n\x07_source\"\xe2\x01\n\x0bRecordQuery\x12\x14\n\x0c\x63\x61tegory_ids\x18\x01 \x03(\x03\x12\x1b\n\x0e\x66rom_timestamp\x18\x02 \x01(\x03H\x00\x88\x01\x01\x12\x19\n\x0cto_timestamp\x18\x03 \x01(\x03H\x01\x88\x01\x01\x12\x13\n\x06offset\x18\x04 \x01(\x03H\x02\x88\x01\x01\x12\x12\n\x05limit\x18\x05 \x01(\x03H\x03\x88\x01\x01\x12\x0f\n\x07user_id\x18\x06 \x01(\x05\x12\x12\n\nwith_group\x18\x07 \x01(\x08\x42\x11\n\x0f_from_timestampB\x0f\n\r_to_timestampB\t\n\x07_offsetB\x08\n\x06_limit\"9\n\x10MultiRecordQuery\x12%\n\x07queries\x18\x01 \x03(\x0b\x32\x14.records.RecordQuery\"9\n\x11MultiRecordAnswer\x12$\n\x07\x61nswers\x18\x01 \x03(\x0b\x32\x13.records.RecordList2\xc7\x03\n\x07Records\x12:\n\x0fGetCategoryList\x12\x0e.records.Empty\x1a\x15.records.CategoryList\"\x00\x12@\n\x16GetCategoryListForUser\x12\r.records.User\x1a\x15.records.CategoryList\"\x00\x12:\n\rGetRecordById\x12\x16.records.RecordRequest\x1a\x0f.records.Record\"\x00\x12;\n\x13GetLastGroupForUser\x12\r.records.User\x1a\x13.records.RecordList\"\x00\x12\x39\n\nGetRecords\x12\x14.records.RecordQuery\x1a\x13.records.RecordList\"\x00\x12M\n\x12GetMultipleRecords\x12\x19.records.MultiRecordQuery\x1a\x1a.records.MultiRecordAnswer\"\x00\x12;\n\x0c\x43ountRecords\x12\x14.records.RecordQuery\x1a\x13.records.RecordList\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protocol.records_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _globals['_EMPTY']._serialized_start=35
  _globals['_EMPTY']._serialized_end=42
  _globals['_USER']._serialized_start=44
  _globals['_USER']._serialized_end=62
  _globals['_RECORDREQUEST']._serialized_start=64
  _globals['_RECORDREQUEST']._serialized_end=91
  _globals['_CATEGORYLIST']._serialized_start=93
  _globals['_CATEGORYLIST']._serialized_end=146
  _globals['_CATEGORY']._serialized_start=149
  _globals['_CATEGORY']._serialized_end=531
  _globals['_RECORDLIST']._serialized_start=533
  _globals['_RECORDLIST']._serialized_end=594
  _globals['_RECORDSOURCE']._serialized_start=596
  _globals['_RECORDSOURCE']._serialized_end=648
  _globals['_RECORDFILE']._serialized_start=650
  _globals['_RECORDFILE']._serialized_end=702
  _globals['_RECORD']._serialized_start=705
  _globals['_RECORD']._serialized_end=968
  _globals['_RECORDQUERY']._serialized_start=971
  _globals['_RECORDQUERY']._serialized_end=1197
  _globals['_MULTIRECORDQUERY']._serialized_start=1199
  _globals['_MULTIRECORDQUERY']._serialized_end=1256
  _globals['_MULTIRECORDANSWER']._serialized_start=1258
  _globals['_MULTIRECORDANSWER']._serialized_end=1315
  _globals['_RECORDS']._serialized_start=1318
  _globals['_RECORDS']._serialized_end=1773
# @@protoc_insertion_point(module_scope)
