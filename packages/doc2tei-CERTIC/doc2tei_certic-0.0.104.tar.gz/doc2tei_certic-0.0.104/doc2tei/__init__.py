import logging
import re
import fnmatch
from typing import List, Tuple
import os
import os.path
import sys
from subprocess import Popen, PIPE
import shutil
from xml.etree import ElementTree as ET
import glob
import base64
from typing import Union

SOFFICE_PATH = shutil.which("soffice")
JAVA_PATH = shutil.which("java")
RESOURCES_PATH = os.path.dirname(os.path.abspath(__file__)) + "/resources/"
SAXON_PATH = os.getenv("SAXON_PATH") or (RESOURCES_PATH + "saxon9.jar")
XMLLINT_PATH = shutil.which("xmllint")

if not SOFFICE_PATH:
    sys.exit("Could not find soffice. Is it in your PATH ?")
if not JAVA_PATH:
    sys.exit("Could not find java. Is it in your PATH ?")
if not SAXON_PATH:
    sys.exit(
        "Could not find the Saxon jar. Please set SAXON_PATH environment variable."
    )
if not os.path.isfile(SAXON_PATH):
    sys.exit(
        "Could not find the Saxon jar. Please check your SAXON_PATH environment variable."
    )
if not XMLLINT_PATH:
    sys.exit("Could not find xmllint. Is it in your PATH ?")


def _silent_remove(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def _union_java_output(std_out: bytes, std_err: bytes) -> Union[bytes, str]:
    """
    Java outputs errors to STDOUT ???
    """
    if std_err:
        try:
            out = std_err.decode("utf-8")
            out = out.strip()
            if out:
                return out
        except UnicodeDecodeError:
            return std_err
    if std_out:
        try:
            out = std_out.decode("utf-8")
            out = out.strip()
            if out:
                return out
        except UnicodeDecodeError:
            return std_out
    return "subprocess provided no error output"


def _find_files(what: str, where: str = ".") -> List[str]:
    rule = re.compile(fnmatch.translate(what), re.IGNORECASE)
    return [
        "{}{}{}".format(where, os.path.sep, name)
        for name in os.listdir(where)
        if rule.match(name)
    ]


def _cli_exec(cli_args: list, logger: logging.Logger) -> Tuple[int, bytes, bytes]:
    logger.debug(" ".join(cli_args))
    p = Popen(
        cli_args,
        stdout=PIPE,
        stderr=PIPE,
    )
    out, err = p.communicate()
    err_code = p.returncode
    p.terminate()
    return err_code, out, err


def _clean_transient_files(transient_files: list, keep_them: bool = False):
    if not keep_them:
        for transient_file_path in transient_files:
            _silent_remove(transient_file_path)


def _check_validation_schema(schema_name: str, logger: logging.Logger) -> str:
    valid_validation_schemas = ["metopes", "openedition"]
    if schema_name not in valid_validation_schemas:
        logger.warning(
            f"{schema_name} validation schema not available. Forcing metopes validation schema."
        )
        return "metopes"
    return schema_name


def _log_xml_error(saxon_output: bytes, logger: logging.Logger) -> bool:
    has_fatal = False
    control_xml = ET.fromstring(saxon_output.decode("utf-8"))
    for error_node in control_xml.findall(".//{*}ERROR"):
        logger.error(error_node.text)
        has_fatal = True
    return has_fatal


def _log_xml_warning(saxon_output: bytes, logger: logging.Logger) -> bool:
    has_error = False
    control_xml = ET.fromstring(saxon_output.decode("utf-8"))
    for error_node in control_xml.findall(".//{*}WARNING"):
        logger.warning(error_node.text)
        has_error = True
    return has_error


def _write_binary_to_file(
    file_path: str, content: bytes, logger: logging.Logger
) -> bool:
    with open(file_path, "wb") as f:
        f.write(content)
        logger.debug("Wrote {}".format(os.path.basename(file_path)))
    return True


def _call_saxon(
    xsl_path: str,
    source_path: str,
    destination_path: str,
    logger: logging.Logger,
    transient_files: list,
) -> Tuple[bool, str]:
    return_code, out, err = _cli_exec(
        [
            JAVA_PATH,
            "-jar",
            SAXON_PATH,
            source_path,
            RESOURCES_PATH + xsl_path,
        ],
        logger,
    )
    if return_code != 0:
        java_out = _union_java_output(out, err)
        if type(java_out) == str:
            return False, java_out
        else:
            return False, java_out.decode("utf-8")
    if _write_binary_to_file(destination_path, out, logger):
        transient_files.append(destination_path)
        if _log_xml_error(out, logger):
            return False, "Not OK"
        _log_xml_warning(out, logger)
        return True, "OK"
    return False, "Not OK"


def _process_doc(
    doc_file,
    working_dir: str,
    logger: logging.Logger,
    keep_transient_files: bool = False,
    validation_schema: str = "metopes",
) -> Tuple[bool, Union[str, bytes]]:
    validation_schema = _check_validation_schema(validation_schema, logger)
    doc_file_no_extension = os.path.splitext(doc_file)[0]
    transient_files = [doc_file]
    #
    # CONVERSION  XML
    #
    transient_files.append(os.path.join(working_dir, doc_file_no_extension + ".xml"))
    return_code, out, err = _cli_exec(
        [
            SOFFICE_PATH,
            "--invisible",
            "--convert-to",
            "xml:OpenDocument Text Flat XML",
            "--outdir",
            working_dir,
            doc_file,
        ],
        logger,
    )

    if return_code != 0:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, _union_java_output(out, err)
    else:
        os.rename(
            os.path.join(
                working_dir,
                doc_file_no_extension + ".xml",
            ),
            os.path.join(working_dir, doc_file_no_extension + "_00.xml"),
        )
        logger.debug(
            "Wrote {}".format(os.path.basename(doc_file_no_extension + "_00.xml"))
        )
        transient_files.append(doc_file_no_extension + "_00.xml")

    #
    # TRANSFORMATIONS XSL : 1 cleanup
    #

    success, output = _call_saxon(
        xsl_path="xsl-01-cleanup/cleanup.xsl",
        source_path=f"{doc_file_no_extension}_00.xml",
        destination_path=f"{doc_file_no_extension}_01_clean.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 2 normalisation (3 steps)
    #

    # Normalize, step 1
    success, output = _call_saxon(
        xsl_path="xsl-02-normalisation/a-normalize-stylename.xsl",
        source_path=f"{doc_file_no_extension}_01_clean.xml",
        destination_path=f"{doc_file_no_extension}_02a_normalize.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    # Normalize step 2
    success, output = _call_saxon(
        xsl_path="xsl-02-normalisation/b-normalize-nodes.xsl",
        source_path=f"{doc_file_no_extension}_02a_normalize.xml",
        destination_path=f"{doc_file_no_extension}_02b_normalize.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    # Normalize, step 3
    success, output = _call_saxon(
        xsl_path="xsl-02-normalisation/c-normalize-groupspan.xsl",
        source_path=f"{doc_file_no_extension}_02b_normalize.xml",
        destination_path=f"{doc_file_no_extension}_02c_normalize.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 3 enrich
    #
    success, output = _call_saxon(
        xsl_path="xsl-03-enrich/enrich.xsl",
        source_path=f"{doc_file_no_extension}_02c_normalize.xml",
        destination_path=f"{doc_file_no_extension}_03_enrich.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (a:sp)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-sp.xsl",
        source_path=f"{doc_file_no_extension}_03_enrich.xml",
        destination_path=f"{doc_file_no_extension}_04a_sp.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (b:quote)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-cit.xsl",
        source_path=f"{doc_file_no_extension}_04a_sp.xml",
        destination_path=f"{doc_file_no_extension}_04b_cit.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (c:figure)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-figure.xsl",
        source_path=f"{doc_file_no_extension}_04b_cit.xml",
        destination_path=f"{doc_file_no_extension}_04c_fig.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (cbis:figure-grp)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-figure-grp.xsl",
        source_path=f"{doc_file_no_extension}_04c_fig.xml",
        destination_path=f"{doc_file_no_extension}_04c-bis_fig.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (d:recension)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-review.xsl",
        source_path=f"{doc_file_no_extension}_04c-bis_fig.xml",
        destination_path=f"{doc_file_no_extension}_04d_review.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (dbis:review hierarchise)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/hierarchize-review.xsl",
        source_path=f"{doc_file_no_extension}_04d_review.xml",
        destination_path=f"{doc_file_no_extension}_04e_review.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (e:floatingText)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/group-floatingText.xsl",
        source_path=f"{doc_file_no_extension}_04e_review.xml",
        destination_path=f"{doc_file_no_extension}_04f_floatingText.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 4 group (ebis:floatingText hierarchise)
    #
    success, output = _call_saxon(
        xsl_path="xsl-04-group/hierarchize-floatingText.xsl",
        source_path=f"{doc_file_no_extension}_04f_floatingText.xml",
        destination_path=f"{doc_file_no_extension}_04g_floatingText.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 5 control hierarchy
    #
    success, output = _call_saxon(
        xsl_path="xsl-05-control/control-hierarchy.xsl",
        source_path=f"{doc_file_no_extension}_04g_floatingText.xml",
        destination_path=f"{doc_file_no_extension}_05_control.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 6 hierarchize
    #
    success, output = _call_saxon(
        xsl_path="xsl-06-hierarchize/hierarchize.xsl",
        source_path=f"{doc_file_no_extension}_05_control.xml",
        destination_path=f"{doc_file_no_extension}_06_hierarchize.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 7 organise
    #
    success, output = _call_saxon(
        xsl_path="xsl-07-organise/organise.xsl",
        source_path=f"{doc_file_no_extension}_06_hierarchize.xml",
        destination_path=f"{doc_file_no_extension}_07_organise.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 8 to TEI
    #
    success, output = _call_saxon(
        xsl_path="xsl-08-totei/totei.xsl",
        source_path=f"{doc_file_no_extension}_07_organise.xml",
        destination_path=f"{doc_file_no_extension}_08_tei.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 9 control styles and id
    #
    success, output = _call_saxon(
        xsl_path="xsl-05-control/control-styles-id.xsl",
        source_path=f"{doc_file_no_extension}_08_tei.xml",
        destination_path=f"{doc_file_no_extension}_09_tei_plus.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    #
    # TRANSFORMATIONS XSL : 10 suppression des erreurs
    #
    success, output = _call_saxon(
        xsl_path="xsl-05-control/control-errors.xsl",
        source_path=f"{doc_file_no_extension}_09_tei_plus.xml",
        destination_path=f"{doc_file_no_extension}_10_tei_metopes.xml",
        logger=logger,
        transient_files=transient_files,
    )
    if not success:
        _clean_transient_files(transient_files, keep_transient_files)
        return False, output

    if validation_schema == "metopes":
        #
        # VALIDATION METOPES
        #
        return_code, out, err = _cli_exec(
            [
                XMLLINT_PATH,
                "--relaxng",
                RESOURCES_PATH + "schema/metopes.rng",
                doc_file_no_extension + "_10_tei_metopes.xml",
            ],
            logger,
        )
        transient_files.append(doc_file_no_extension + "_10_tei_metopes.xml")
        if return_code != 0:
            logger.error(
                "Validate {} {}".format(
                    os.path.basename(doc_file_no_extension + "_10_tei_metopes.xml"),
                    _union_java_output(out, err),
                )
            )
        else:
            logger.info(
                "Validate {}".format(
                    os.path.basename(
                        doc_file_no_extension
                        + "_10_tei_metopes.xml validates {}".format(validation_schema)
                    )
                )
            )
    elif validation_schema == "openedition":
        #
        # TRANSFORMATIONS XSL : 11 to OpenEdition
        #
        success, output = _call_saxon(
            xsl_path="xsl-09-toOpenedition/toOpenedition.xsl",
            source_path=f"{doc_file_no_extension}_10_tei_metopes.xml",
            destination_path=f"{doc_file_no_extension}_11_tei_openedition.xml",
            logger=logger,
            transient_files=transient_files,
        )
        if not success:
            _clean_transient_files(transient_files, keep_transient_files)
            return False, output

        #
        # VALIDATION OPENEDITION
        #
        return_code, out, err = _cli_exec(
            [
                XMLLINT_PATH,
                #      "--valid",
                "--relaxng",
                "http://lodel.org/ns/tei/draft/commons-publishing-openedition.rng",
                doc_file_no_extension + "_11_tei_openedition.xml",
                #     "--noout",
            ],
            logger,
        )
        if return_code != 0:
            logger.error(
                "Validate {} {}".format(
                    os.path.basename(doc_file_no_extension + "_11_tei_openedition.xml"),
                    _union_java_output(out, err),
                )
            )
        else:
            logger.info(
                "Validate {}".format(
                    os.path.basename(
                        doc_file_no_extension
                        + "_11_tei_openedition.xml validates {}".format(
                            validation_schema
                        )
                    )
                )
            )
    #
    # TRAITEMENT DES IMAGES
    #
    for b64_path in glob.glob(working_dir + "/images/*.base64"):
        destination_path, _ = os.path.splitext(b64_path)
        with open(destination_path, "wb") as destination_file:
            with open(b64_path, "rb") as b64_file:
                destination_file.write(base64.decodebytes(b64_file.read()))
        _silent_remove(b64_path)

    final_file_destination = os.path.join(working_dir, doc_file_no_extension + ".xml")
    if validation_schema == "metopes":
        shutil.copy(
            os.path.join(working_dir, doc_file_no_extension + "_10_tei_metopes.xml"),
            final_file_destination,
        )
    if validation_schema == "openedition":
        shutil.copy(
            os.path.join(
                working_dir, doc_file_no_extension + "_11_tei_openedition.xml"
            ),
            final_file_destination,
        )
    transient_files.remove(final_file_destination)
    _clean_transient_files(transient_files, keep_transient_files)

    return True, "All OK"


def doc2tei(working_dir: str, logger: logging.Logger, options: dict = None):
    options = options or {}
    keep_transient_files = False
    if options.get("keep_transient_files", False) == "oui":
        keep_transient_files = True
    success_counter = 0
    failure_counter = 0
    doc_files = _find_files("*.docx", working_dir) + _find_files("*.odt", working_dir)
    logger.info("{} file(s) to convert.".format(len(doc_files)))
    for doc_file in doc_files:
        logger.info("converting {}".format(os.path.basename(doc_file)))
        success, output = _process_doc(
            doc_file,
            working_dir,
            logger,
            keep_transient_files,
            options.get("validation_schema", "metopes"),
        )
        if not success:
            logger.error(
                "could not convert {}. Process output: {}".format(
                    os.path.basename(doc_file), output
                )
            )
            failure_counter = failure_counter + 1
        else:
            success_counter = success_counter + 1
            logger.info("{}: success".format(os.path.basename(doc_file)))
    logger.info("Job done, {} files converted".format(success_counter))


doc2tei.description = {
    "label": "Docx vers TEI",
    "help": "Convertir les fichiers *.docx et *.odt en fichiers *.xml (vocabulaire TEI)",
    "options": [
        {
            "id": "keep_transient_files",
            "label": "garder les fichiers intermédiaires",
            "values": {"oui": "oui", "non": "non"},
            "default": "non",
            "free_input": False,
        },
        {
            "id": "validation_schema",
            "label": "schéma de validation",
            "values": {"metopes": "Métopes", "openedition": "openedition"},
            "default": "metopes",
            "free_input": False,
        },
    ],
}
