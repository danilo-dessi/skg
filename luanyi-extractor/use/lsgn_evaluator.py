import traceback
import datetime
import time
import pandas

import coref_metrics
import debug_utils
import inference_utils
from input_utils import pad_batch_tensors
import operator
import srl_eval_utils
import util


class LSGNEvaluator(object):
  def __init__(self, config):
    self.config = config
    self.eval_data = None

  # TODO: Split to multiple functions.
  def evaluate(self, session, data, predictions, loss, official_stdout=False):
    if self.eval_data is None:
      self.eval_data, self.eval_tensors, self.coref_eval_data = data.load_eval_data()

    def _k_to_tag(k):
      if k == -3:
        return "oracle"
      elif k == -2:
        return "actual"
      elif k == -1:
        return "exact"
      elif k == 0:
        return "threshold"
      else:
        return "{}%".format(k)

    # Retrieval evaluators.
    arg_evaluators = { k:util.RetrievalEvaluator() for k in [-3, -2, -1, 30, 40, 50, 80, 100, 120, 150] }
    predicate_evaluators = { k:util.RetrievalEvaluator() for k in [-3, -2, -1, 10, 20, 30, 40, 50, 70] }
    mention_evaluators = { k:util.RetrievalEvaluator() for k in [-3, -2, -1, 10, 20, 30, 40, 50] }
    entity_evaluators = { k:util.RetrievalEvaluator() for k in [-3, -2, -1, 10, 20, 30, 40, 50, 70] }

    total_loss = 0
    total_num_predicates = 0
    total_gold_predicates = 0

    srl_comp_sents = 0
    srl_predictions = []
    ner_predictions = []
    rel_predictions = []
    coref_predictions = {}
    coref_evaluator = coref_metrics.CorefEvaluator()
    all_gold_predicates = []
    all_guessed_predicates = []

    start_time = time.time()
    debug_printer = debug_utils.DebugPrinter()

    # Simple analysis.
    unique_core_role_violations = 0
    continuation_role_violations = 0
    reference_role_violations = 0
    gold_u_violations = 0
    gold_c_violations = 0
    gold_r_violations = 0

    # Global sentence ID.
    rel_sent_id = 0
    srl_sent_id = 0
    file_sentences = []
    file_entities = []
    file_relations = []

    mydata = {'sentences' : [], 'entities' : [], 'relations' : []}

    for i, doc_tensors in enumerate(self.eval_tensors):
      
      try:
        feed_dict = dict(zip(
                data.input_tensors,
                [pad_batch_tensors(doc_tensors, tn) for tn in data.input_names + data.label_names]))
        predict_names = []
        for tn in data.predict_names:
            if tn in predictions:
                predict_names.append(tn)
        predict_tensors = [predictions[tn] for tn in predict_names] + [loss]
        predict_tensors = session.run(predict_tensors, feed_dict=feed_dict)
        predict_dict = dict(zip(predict_names + ["loss"], predict_tensors))


        doc_size = len(doc_tensors)
        doc_example = self.coref_eval_data[i]
        sentences = doc_example["sentences"]
        decoded_predictions = inference_utils.mtl_decode(
            sentences, predict_dict, data.ner_labels_inv, data.rel_labels_inv,
            self.config)
      except:
            print(traceback.format_exc())
            print('Problem on ', str(i), 'document')
            continue
    
      print "FILE N #" + str(i)  
      
      file_sentences = []
      file_entities = []
      file_relations = []

      for s, ner, rel  in zip(sentences, decoded_predictions['ner'], decoded_predictions['rel']):
          file_sentences += [' '.join(s)]
          tmp_entities = []
          for ner_item in ner:
              start = int(ner_item[0]) 
              end = int(ner_item[1]) + 1
              tmp_entities += [(' '.join(s[start:end]), ner_item[2])]

          file_entities += [tmp_entities]
          
          
          tmp_relations = []
          for rel_element in rel:
              start_e1 = int(rel_element[0])
              end_e1 = int(rel_element[1]) + 1
              start_e2 = int(rel_element[2])
              end_e2 = int(rel_element[3]) + 1
              tmp_relations += [(' '.join(s[start_e1:end_e1]), rel_element[4] , ' '.join(s[start_e2:end_e2]))]
          file_relations += [tmp_relations]
      
      
      mydata['sentences'] += [file_sentences]
      mydata['entities'] += [file_entities]
      mydata['relations'] += [file_relations]
      dataframe = pandas.DataFrame.from_dict(mydata)
      dataframe.to_csv('csv_e_r/miachiave.csv')
      exit(1)