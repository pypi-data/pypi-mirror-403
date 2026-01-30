import numpy as np
from sklearn.decomposition import PCA

RANDOM_STATE = 42


def get_pca_statistics(
    data: np.ndarray, random_state: int = RANDOM_STATE
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Вычисляет статистику по PCA.

    Parameters
    ----------
    data: np.ndarray
        Массив значений, размера (N, M).
    random_state: int
        Определяет генерацию случайных чисел.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Массив собственных значений, размера N.
        Массив процентов дисперсии, объясняемых каждым из выбранных компонентов, размера N.
        Массив суммированных процентов дисперсии, размера N.
    """

    assert data.ndim == 2, "data: Ожидался 2D массив"

    pca = PCA(n_components=data.shape[1], random_state=random_state)
    pca.fit(data)
    explained_variance_ratio = pca.explained_variance_ratio_
    sum_explained_variance_ratio = explained_variance_ratio.copy()
    for i in range(1, len(explained_variance_ratio)):
        sum_explained_variance_ratio[i] += sum_explained_variance_ratio[i - 1]
    return pca.singular_values_, explained_variance_ratio, sum_explained_variance_ratio


def pca_transform(
    data: np.ndarray, n_components: int, random_state: int = RANDOM_STATE
) -> np.ndarray:
    """
    Понижение размерности с помощью PCA путём проецирования данных на главные (собственные) вектора.

    Parameters
    ----------
    data: np.ndarray
        Массив значений, размера (N, M).
    n_components: int
        Количество сохраняемых компонентов.
    random_state: int
        Определяет генерацию случайных чисел.

    Returns
    -------
    np.ndarray
        Преобразованный массив, размера (N, n_components).
    """

    assert data.ndim == 2, "data: Ожидался 2D массив"
    assert (
        n_components > 0
    ), "Параметр n_components должен принимать положительное значение"

    return PCA(n_components=n_components, random_state=random_state).fit_transform(data)
