from logger_local.LoggerComponentEnum import LoggerComponentEnum

LANGUAGE_REMOTE_PYTHON_COMPONENT_ID = 288
LANGUAGE_REMOTE_PYTHON_COMPONENT_NAME = "language-remote-python-package"
DEVELOPER_EMAIL = "tal.g@circ.zone"
LANGUAGE_REMOTE_PYTHON_PACKAGE_CODE_LOGGER_OBJECT = {
    'component_id': LANGUAGE_REMOTE_PYTHON_COMPONENT_ID,
    'component_name': LANGUAGE_REMOTE_PYTHON_COMPONENT_NAME,
    'component_category': LoggerComponentEnum.ComponentCategory.Code.value,
    'developer_email': DEVELOPER_EMAIL
}


LANGUAGE_REMOTE_PYTHON_PACKAGE_TEST_LOGGER_OBJECT = {
    'component_id': LANGUAGE_REMOTE_PYTHON_COMPONENT_ID,
    'component_name': LANGUAGE_REMOTE_PYTHON_COMPONENT_NAME,
    'component_category': LoggerComponentEnum.ComponentCategory.Unit_Test.value,
    'testing_framework': LoggerComponentEnum.testingFramework.pytest.value,
    'developer_email': DEVELOPER_EMAIL
}