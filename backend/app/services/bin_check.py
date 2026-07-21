"""ҚР БСН/ЖСН чексум-алгоритмі.

12 цифр: алғашқы 11-і салмақпен қосылып, mod 11 нәтижесі 12-цифрға тең болуы
керек. Нәтиже 10 шықса, екінші салмақ жиынтығымен қайта есептеледі; ол да 10
болса, нөмір жарамсыз. Бұл тек синтаксистік тексеру: нөмірдің реестрде бар-жоғын
айтпайды (оны stat.gov.kz lookup шешеді, келесі кезеңде).
"""

WEIGHTS_FIRST = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
WEIGHTS_SECOND = (3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2)


def is_valid_bin(value: str) -> bool:
    if len(value) != 12 or not value.isdigit():
        return False
    digits = [int(c) for c in value]
    checksum = sum(w * d for w, d in zip(WEIGHTS_FIRST, digits[:11])) % 11
    if checksum == 10:
        checksum = sum(w * d for w, d in zip(WEIGHTS_SECOND, digits[:11])) % 11
        if checksum == 10:
            return False
    return checksum == digits[11]
