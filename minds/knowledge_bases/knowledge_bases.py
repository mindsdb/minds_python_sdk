from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from minds.rest_api import RestAPI


class VectorStoreConfig(BaseModel):
    '''Configuration for the underlying vector store for knowledge base embeddings'''
    engine: str
    connection_data: Dict[str, Any]
    table: str = 'embeddings'


class EmbeddingConfig(BaseModel):
    '''Configuration for embeddings to use with underlying vector store for knowledge base'''
    provider: str
    model: str
    params: Optional[Dict[str, Any]] = None


class KnowledgeBaseConfig(BaseModel):
    '''Configuration for a knowledge base'''
    name: str
    description: str
    vector_store_config: Optional[VectorStoreConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None


class KnowledgeBaseDocument(BaseModel):
    '''Represents a document that can be inserted into a knowledge base'''
    id: Union[int, str]
    content: str
    metadata: Optional[Dict[str, Any]] = {}


class KnowledgeBase:
    def __init__(self, name, api: RestAPI):
        self.name = name
        self.api = api

    def insert_from_select(self, query: str):
        '''
        Inserts select content of a connected datasource into this knowledge base

        :param query: The SQL SELECT query to use to retrieve content to be inserted
        '''
        update_request = {
            'query': query
        }
        _ = self.api.put(f'/knowledge_bases/{self.name}', data=update_request)

    def insert_documents(self, documents: List[KnowledgeBaseDocument]):
        '''
        Inserts documents directly into this knowledge base

        :param documents: The documents to insert
        '''
        update_request = {
            'rows': [d.model_dump() for d in documents]
        }
        _ = self.api.put(f'/knowledge_bases/{self.name}', data=update_request)

    def insert_urls(self, urls: List[str]):
        '''
        Crawls URLs & inserts the retrieved webpages into this knowledge base

        :param urls: Valid URLs to crawl & insert
        '''
        update_request = {
            'urls': urls
        }
        _ = self.api.put(f'/knowledge_bases/{self.name}', data=update_request)

    def insert_files(self, files: List[str]):
        '''
        Inserts files that have already been uploaded to MindsDB into this knowledge base

        :param files: Names of preuploaded files to insert
        '''
        update_request = {
            'files': files
        }
        _ = self.api.put(f'/knowledge_bases/{self.name}', data=update_request)


class KnowledgeBases:
    def __init__(self, client):
        self.api = client.api

    def create(self, config: KnowledgeBaseConfig) -> KnowledgeBase:
        '''
        Create new knowledge base and return it

        :param config: knowledge base configuration, properties:
           - name: str, name of knowledge base
           - description: str, description of the knowledge base. Used by minds to know what data can be retrieved.
           - vector_store_config: VectorStoreConfig, configuration for embeddings vector store.
           - embedding_config: EmbeddingConfig, configuration for embeddings.
        :return: knowledge base object
        '''
        create_request = {
            'name': config.name,
            'description': config.description
        }
        if config.vector_store_config is not None:
            vector_store_data = {
                'engine': config.vector_store_config.engine,
                'connection_data': config.vector_store_config.connection_data
            }
            create_request['vector_store'] = vector_store_data
        if config.embedding_config is not None:
            embedding_data = {
                'provider': config.embedding_config.provider,
                'name': config.embedding_config.model
            }
            if config.embedding_config.params is not None:
                embedding_data.update(config.embedding_config.params)
            create_request['embedding_model'] = embedding_data

        _ = self.api.post('/knowledge_bases', data=create_request)
        return self.get(config.name)

    def list(self) -> List[KnowledgeBase]:
        '''
        Returns list of knowledge bases

        :return: iterable knowledge bases
        '''

        list_knowledge_bases_response = self.api.get('/knowledge_bases')
        knowledge_bases = list_knowledge_bases_response.json()

        all_knowledge_bases = []
        for knowledge_base in knowledge_bases:
            all_knowledge_bases.append(KnowledgeBase(knowledge_base['name'], self.api))
        return all_knowledge_bases

    def get(self, name: str) -> KnowledgeBase:
        '''
        Get knowledge base by name

        :param name: name of knowledge base
        :return: knowledge base object
        '''

        knowledge_base_response = self.api.get(f'/knowledge_bases/{name}')
        knowledge_base = knowledge_base_response.json()
        return KnowledgeBase(knowledge_base['name'], self.api)

    def drop(self, name: str, force=False):
        '''
        Drop knowledge base by name

        :param name: name of knowledge base
        :param force: if True - remove from all minds, default: False
        '''
        data = None
        if force:
            data = {'cascade': True}

        self.api.delete(f'/knowledge_bases/{name}', data=data)
