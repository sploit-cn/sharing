from elasticsearch.dsl import Text, Keyword, Integer, Boolean, Completion, analyzer, token_filter, AsyncDocument

my_pinyin = token_filter(
    'my_pinyin', type='pinyin', keep_full_pinyin=False,
    keep_joined_full_pinyin=True,
    keep_original=True,
    limit_first_letter_length=16,
    remove_duplicated_term=True,
    none_chinese_pinyin_tokenize=False)

ik_max_pinyin = analyzer(
    'ik_max_pinyin', tokenizer='ik_max_word', filter=my_pinyin)


class Project(AsyncDocument):
  name = Text(fields={'suggest': Completion(
      analyzer="keyword", search_analyzer="keyword")}, analyzer=ik_max_pinyin, search_analyzer="ik_smart")
  brief = Text(analyzer=ik_max_pinyin, search_analyzer="ik_smart")
  description = Text(analyzer=ik_max_pinyin, search_analyzer="ik_smart")
  programming_language = Keyword()
  license = Keyword()
  platform = Keyword()
  is_featured = Boolean()
  tags = Integer()

  class Index:
    name = 'projects'
