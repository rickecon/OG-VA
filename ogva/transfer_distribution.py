import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kde
import os

CURDIR = os.path.split(os.path.abspath(__file__))[0]


# Will need to do some smoothing with a KDE when estimate the matrix...
def MVKDE(S, J, proportion_matrix, filename=None, plot=False, bandwidth=0.25):
    """
    Generates a Multivariate Kernel Density Estimator and returns a
    matrix representing a probability distribution according to given
    age categories, and ability type categories.

    Args:
        S (scalar): the number of age groups in the model
        J (scalar): the number of ability type groups in the model.
        proportion_matrix (Numpy array): SxJ shaped array that
            represents the proportions of the total going to each
            (s,j) combination
        filename (str): the file name  to save image to
        plot (bool): whether or not to save a plot of the probability
            distribution generated by the kde or the proportion matrix
        bandwidth (scalar):  used in the smoothing of the kernel. Higher
            bandwidth creates a smoother kernel.

    Returns:
        estimator_scaled (Numpy array): SxJ shaped array that
            that represents the smoothed distribution of proportions
            going to each (s,j)

    """
    proportion_matrix_income = np.sum(proportion_matrix, axis=0)
    proportion_matrix_age = np.sum(proportion_matrix, axis=1)
    age_probs = np.random.multinomial(70000, proportion_matrix_age)
    income_probs = np.random.multinomial(70000, proportion_matrix_income)
    age_frequency = np.array([])
    income_frequency = np.array([])
    age_mesh = complex(str(S) + "j")
    income_mesh = complex(str(J) + "j")
    j = 18
    """creating a distribution of age values"""
    for i in age_probs:
        listit = np.ones(i)
        listit *= j
        age_frequency = np.append(age_frequency, listit)
        j += 1

    k = 1
    """creating a distribution of ability type values"""
    for i in income_probs:
        listit2 = np.ones(i)
        listit2 *= k
        income_frequency = np.append(income_frequency, listit2)
        k += 1

    freq_mat = np.vstack((age_frequency, income_frequency)).T
    density = kde.gaussian_kde(freq_mat.T, bw_method=bandwidth)
    age_min, income_min = freq_mat.min(axis=0)
    age_max, income_max = freq_mat.max(axis=0)
    agei, incomei = np.mgrid[
        age_min:age_max:age_mesh, income_min:income_max:income_mesh
    ]
    coords = np.vstack([item.ravel() for item in [agei, incomei]])
    estimator = density(coords).reshape(agei.shape)
    estimator_scaled = estimator / float(np.sum(estimator))
    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        ax.plot_surface(agei, incomei, estimator_scaled, rstride=5)
        ax.set_xlabel("Age")
        ax.set_ylabel("Ability Types")
        ax.set_zlabel("Received proportion of total transfers")
        plt.savefig(filename)
    return estimator_scaled


def get_transfer_matrix(graphs=False):
    """
    Compute SxJ matrix representing the distribution of aggregate
    government transfers by age and lifetime income group.
    """
    # Create directory if output directory does not already exist
    CURDIR = os.path.split(os.path.abspath(__file__))[0]
    output_fldr = "csv_output_files"
    output_dir = os.path.join(CURDIR, output_fldr)
    if not os.access(output_dir, os.F_OK):
        os.makedirs(output_dir)
    image_fldr = "images"
    image_dir = os.path.join(CURDIR, image_fldr)
    if not os.access(image_dir, os.F_OK):
        os.makedirs(image_dir)

    # Define a lambda function to compute the weighted mean:
    # wm = lambda x: np.average(
    #     x, weights=df.loc[x.index, "fam_smpl_wgt_core"])

    # Read in dataframe of PSID data
    # df = ogcore.utils.safe_read_pickle(
    #     os.path.join(CURDIR, "data", "PSID", "psid_lifetime_income.pkl")
    # )
    df = pd.read_csv(
        os.path.join(CURDIR, "data", "PSID", "psid_lifetime_income.csv")
    )

    # Do some tabs with data file...
    df["total_transfers"] = (
        df["head_and_spouse_transfer_income"]
        + df["other_familyunit_transfer_income"]
    )

    df["sum_transfers"] = (
        df["other_familyunit_ssi_prior_year"]
        + df["head_other_welfare_prior_year"]
        + df["spouse_other_welfare_prior_year"]
        + df["other_familyunit_other_welfare_prior_year"]
        + df["head_unemp_inc_prior_year"]
        + df["spouse_unemp_inc_prior_year"]
        + df["other_familyunit_unemp_inc_prior_year"]
    )

    if graphs:
        # Total total_transfers by year
        df.groupby("year_data").mean().plot(y="total_transfers")
        plt.savefig(os.path.join(image_dir, "total_transfers_year.png"))
        df.groupby("year_data").mean().plot(y="sum_transfers")
        plt.savefig(os.path.join(image_dir, "sum_transfers_year.png"))
        # note that the sum of transfer categories is much lower than the
        # tranfers variable.  The transfers variable goes more to high income
        # and old, even though it says it excludes social security

        # Fraction of total_transfers in a year by age
        # line plot
        df[df["year_data"] >= 1988].groupby("age").mean().plot(
            y="total_transfers"
        )
        plt.savefig(os.path.join(image_dir, "total_transfers_age.png"))

        # total_transfers by lifetime income group
        # bar plot
        df[df["year_data"] >= 1988].groupby("li_group").mean().plot.bar(
            y="total_transfers"
        )
        plt.savefig(os.path.join(image_dir, "total_transfers_li.png"))

        # lifecycle plots with line for each ability type
        pd.pivot_table(
            df[df["year_data"] >= 1988],
            values="total_transfers",
            index="age",
            columns="li_group",
            aggfunc="mean",
        ).plot(legend=True)
        plt.savefig(os.path.join(image_dir, "total_transfers_age_li.png"))

        pd.pivot_table(
            df[df["year_data"] >= 1988],
            values="sum_transfers",
            index="age",
            columns="li_group",
            aggfunc="mean",
        ).plot(legend=True)
        plt.savefig(os.path.join(image_dir, "sum_transfers_age_li.png"))

    # Matrix Fraction of total_transfers in a year by age and lifetime_inc
    total_transfers_matrix = pd.pivot_table(
        df[df["year_data"] >= 1988],
        values="total_transfers",
        index="age",
        columns="li_group",
        aggfunc="sum",
    )
    # replace NaN with zero
    total_transfers_matrix.fillna(value=0, inplace=True)
    total_transfers_matrix = (
        total_transfers_matrix / total_transfers_matrix.sum().sum()
    )
    # total_transfers_matrix.to_csv(os.path.join(
    #     output_dir, 'transfer_matrix.csv'))

    # estimate kernel density of transfers
    kde_matrix = MVKDE(
        80,
        7,
        total_transfers_matrix.to_numpy(),
        filename=os.path.join(image_dir, "total_transfers_kde.png"),
        plot=True,
        bandwidth=0.5,
    )
    np.savetxt(
        os.path.join(output_dir, "total_transfers_kde.csv"),
        kde_matrix,
        delimiter=",",
    )

    return kde_matrix
