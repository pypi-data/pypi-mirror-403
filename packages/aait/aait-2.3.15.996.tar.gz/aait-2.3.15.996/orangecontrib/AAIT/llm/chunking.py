import copy
import re
import os
import pathlib
import Orange
from Orange.data import Domain, Table, StringVariable, ContinuousVariable



### Chonkie
from importlib.metadata import version, PackageNotFoundError
from packaging.version import Version
try:
    chonkie_version = Version(version("chonkie"))
except PackageNotFoundError:
    chonkie_version = None
if chonkie_version is None:
    raise RuntimeError("chonkie is not installed")


elif chonkie_version >= Version("1.5.2"):
    from chonkie import TokenChunker, SentenceChunker, RecursiveChunker, SemanticChunker, LateChunker

    def create_chunks(table, column_name, tokenizer="character", chunk_size=300, chunk_overlap=100, mode="Token",
                      progress_callback=None, argself=None):
        """
        Chunk the text in `column_name` of an Orange Table using a specialized chunker.

        Splits each row's text into chunks based on the selected mode (Token, Sentence,
        Recursive, or Markdown). Adds the chunked text and its metadata as new meta
        columns to the table.

        Parameters:
            table (Table): Input data table.
            column_name (str): Name of the text column to chunk.
            tokenizer (str): Tokenizer type (e.g., "character").
            chunk_size (int): Target chunk size.
            chunk_overlap (int): Overlap between chunks (not used in all modes).
            mode (str): Chunking strategy ("Token", "Sentence", "Recursive", "Markdown").
            progress_callback (callable): Optional progress reporter.
            argself: Optional caller reference.

        Returns:
            Table: The table with added meta columns: "Chunks", "Chunks size", and "Metadata".
        """
        print("This widget is being updated : default tokenizer 'character' enabled for compatibility !!")
        tokenizer = "character"

        # Définir la fonction de chunking selon le mode
        if mode == "Token":
            chunker = TokenChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif mode == "Sentence":
            chunker = SentenceChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                      min_sentences_per_chunk=1)
        elif mode == "Recursive":
            chunker = RecursiveChunker(tokenizer=tokenizer, chunk_size=chunk_size, min_characters_per_chunk=24)

        ### Les 3 modes suivants sont à tester après montée de version !!
        ### Attention à la gestion des modèles !! Tokenizer doit être un SentenceTransformer (Mpnet ou Qwen-0.6B)
        ### Gérer ça en amont dans le widget !
        ### Ajouter du paramétrage selon la méthode de chunking !!!
        elif mode == "Markdown":
            # from recipe, tester dépendances d'abord
            current_dir = pathlib.Path(__file__).parent.resolve()
            chunker = RecursiveChunker.from_recipe(path=os.path.join(current_dir, r"resources\markdown_recipe.json"),
                                                   tokenizer=tokenizer, chunk_size=400, min_characters_per_chunk=24)
        elif mode == "Semantic":
            chunker = SemanticChunker(embedding_model=tokenizer, threshold=0.7, chunk_size=chunk_size)
        elif mode == "Late":
            chunker = LateChunker(embedding_model=tokenizer, chunk_size=chunk_size, min_characters_per_chunk=24)
        else:
            raise ValueError(f"Invalid mode: {mode}. Valid modes are: Token, Sentence, Recursive, Markdown")

        new_metas = list(table.domain.metas) + [StringVariable("Chunks"), ContinuousVariable("Chunks size"),
                                                ContinuousVariable("Chunks index"), ContinuousVariable("Chunks start"),
                                                ContinuousVariable("Chunks end"), StringVariable("Metadata")]
        new_domain = Domain(table.domain.attributes, table.domain.class_vars, new_metas)

        new_rows = []
        for i, row in enumerate(table):
            content = row[column_name].value
            chunks = chunker(content)
            # For each chunk in the chunked data
            for j, chunk in enumerate(chunks):
                # Build new metas with previous data and the chunk
                new_metas_values = list(row.metas) + [chunk.text, chunk.token_count, j, chunk.start_index,
                                                      chunk.end_index, ""]
                # Create the new row instance
                new_instance = Orange.data.Instance(new_domain,
                                                    [row[x] for x in table.domain.attributes] + [row[y] for y in
                                                                                                 table.domain.class_vars] + new_metas_values)
                # Store the new row
                new_rows.append(new_instance)

            if progress_callback is not None:
                progress_value = float(100 * (i + 1) / len(table))
                progress_callback(progress_value)
            if argself is not None:
                if argself.stop:
                    break

        return Table.from_list(domain=new_domain, rows=new_rows)






else: # chonkie_version == Version("0.4.1"):
    from chonkie import TokenChunker, WordChunker, SentenceChunker


    def create_chunks(table, column_name, model, chunk_size=500, overlap=125, mode="words", progress_callback=None,
                      argself=None):
        """
        Chunk the text in `column_name` of an Orange Table.

        Splits each row's text into overlapping chunks (by words or characters),
        optionally reporting progress. Rows producing multiple chunks are duplicated.

        Parameters:
            table (Table): Input data table.
            model: Embedding model used by the chunking pipeline.
            column_name (str): Name of the text column to chunk.
            chunk_size (int): Target chunk size.
            overlap (int): Overlap between chunks.
            mode (str): "words" or "characters".
            progress_callback (callable): Optional progress reporter.
            argself: Optional caller reference.

        Returns:
            Table: A new table with one row per chunk and a "Chunks" column.
        """
        if model is None or isinstance(model, str):
            return

        data = copy.deepcopy(table)

        # Définir la fonction de chunking selon le mode
        # if mode == "tokens":
        #     chunk_function = chunk_tokens
        if mode == "Token":
            chunk_function = chunk_words
        elif mode == "Recursive":
            chunk_function = chunk_words
        elif mode == "Sentence":
            chunk_function = chunk_sentences
        elif mode == "semantic":
            chunk_function = chunk_semantic
        elif mode == "markdown":
            chunk_function = chunk_markdown
        else:
            raise ValueError(
                f"Invalid mode: {mode}. Valid modes are: 'tokens', 'words', 'sentence', 'markdown', 'semantic'")

        # new_metas = [StringVariable("Chunks"), ContinuousVariable("Chunks index"), StringVariable("Metadata")]
        new_metas = list(data.domain.metas) + [StringVariable("Chunks"), ContinuousVariable("Chunks index"),
                                               StringVariable("Metadata")]
        new_domain = Domain(data.domain.attributes, data.domain.class_vars, new_metas)

        new_rows = []
        for i, row in enumerate(data):
            content = row[column_name].value
            chunks, metadatas = chunk_function(content, tokenizer=model.tokenizer, chunk_size=chunk_size,
                                               chunk_overlap=overlap)
            # For each chunk in the chunked data
            for j, chunk in enumerate(chunks):
                # Build a new row with the previous data and the chunk
                if len(metadatas) == 0:
                    new_metas_values = list(row.metas) + [chunk] + [j] + [""]
                else:
                    new_metas_values = list(row.metas) + [chunk] + [j] + [metadatas[j]]
                new_instance = Orange.data.Instance(new_domain,
                                                    [row[x] for x in data.domain.attributes] + [row[y] for y in
                                                                                                data.domain.class_vars] + new_metas_values)
                new_rows.append(new_instance)

        return Table.from_list(domain=new_domain, rows=new_rows)


    def chunk_tokens(content, tokenizer, chunk_size=512, chunk_overlap=128):
        chunker = TokenChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk(content)
        chunks = [chunk.text for chunk in chunks]
        return chunks, []


    def chunk_words(content, tokenizer, chunk_size=300, chunk_overlap=100):
        chunker = WordChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk(content)
        chunks = [chunk.text for chunk in chunks]
        return chunks, []


    def chunk_sentences(content, tokenizer, chunk_size=500, chunk_overlap=125):
        chunker = SentenceChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                  min_sentences_per_chunk=1)
        chunks = chunker.chunk(content)
        chunks = [chunk.text for chunk in chunks]
        return chunks, []


    def chunk_markdown(content, tokenizer=None, chunk_size=500, chunk_overlap=125):
        """
        Découpe un contenu Markdown en chunks :
        - Si des en-têtes Markdown (#, ##, ###...) existent : on respecte la hiérarchie
          et on inclut dans les métadonnées uniquement les titres de la branche courante.
        - Sinon : on délègue à chunk_words().

        Parameters
        ----------
        content : str
            Le contenu (Markdown ou texte brut).
        tokenizer : any
            Tokenizer utilisé par WordChunker si besoin.
        chunk_size : int
            Nombre max de mots par chunk.
        chunk_overlap : int
            Overlap (en mots) entre deux chunks consécutifs.

        Returns
        -------
        (chunks, metadatas) : tuple(list[str], list[str])
            chunks : segments de texte
            metadatas : hiérarchies de titres associées (chaînes " ; " séparées), vide si aucun titre.
        """
        if not content or not isinstance(content, str):
            return [], []

        header_regex = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
        matches = list(header_regex.finditer(content))

        # Cas SANS en-têtes : appel direct à chunk_words
        if not matches:
            chunks, _ = chunk_words(content, tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            return chunks, [""] * len(chunks)

        # Cas AVEC en-têtes : extraire les sections (level, title, body)
        sections = []
        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip()
            sections.append((level, title, body))

        chunks, metadatas = [], []
        current_titles = {}

        for level, title, body in sections:
            # purge les niveaux >= level
            for l in list(current_titles.keys()):
                if l >= level:
                    current_titles.pop(l, None)
            current_titles[level] = title

            metadata = " ; ".join(current_titles[lvl] for lvl in sorted(current_titles) if lvl <= level)

            # déléguer le découpage de body à chunk_words
            body_chunks, _ = chunk_words(body, tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            for ch in body_chunks:
                chunks.append(ch)
                metadatas.append(metadata)

        return chunks, metadatas


    def chunk_semantic():
        pass