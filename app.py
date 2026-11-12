import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

from genetic_algorithm import genetic_algorithm


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="TV Scheduling Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# STYLING
# ==================================================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }

        .hero {
            padding: 2rem 2.2rem;
            border-radius: 18px;
            background: linear-gradient(120deg, #183153, #254e77);
            color: #ffffff;
            margin-bottom: 1.6rem;
        }

        .hero-label {
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: #c4dcf4;
            margin-bottom: 0.65rem;
        }

        .hero-title {
            font-size: clamp(1.8rem, 3vw, 2.7rem);
            line-height: 1.15;
            font-weight: 750;
            margin-bottom: 0.65rem;
        }

        .hero-description {
            font-size: 1rem;
            line-height: 1.6;
            color: #e0ebf5;
            max-width: 760px;
        }

        div[data-testid="stMetric"] {
            padding: 1.2rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 12px;
            height: 100%;
        }

        div[data-testid="stMetricValue"] {
            font-weight: 700;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            border-radius: 9px;
            font-weight: 600;
            min-height: 44px;
        }

        @media (max-width: 600px) {
            .hero {
                padding: 1.5rem;
            }

            .block-container {
                padding-top: 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# CONSTANTS
# ==================================================

GENERATIONS = 100
POPULATION_SIZE = 50
ELITISM_SIZE = 2
RANDOM_SEED = 42
MAX_TRIALS = 3

CSV_PATH = (
    Path(__file__).resolve().parent
    / "program_ratings_modified.csv"
)


# ==================================================
# SESSION STATE
# ==================================================

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "saved_trials" not in st.session_state:
    st.session_state.saved_trials = []


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def readable_program_name(program):
    """Make programme names easier to read."""
    return program.replace("_", " ").title()


def create_schedule_dataframe(schedule, ratings):
    """Create the schedule table from the algorithm result."""
    rows = []

    for index, program in enumerate(schedule):
        rows.append({
            "Time Slot": f"{index + 6:02d}:00",
            "Programme": readable_program_name(program),
            "Rating": ratings[program][index]
        })

    return pd.DataFrame(rows)


def validate_schedule(schedule, programs):
    """Check the requirements implemented by this app."""
    expected_programs = set(programs)

    return (
        len(schedule) == 18
        and len(expected_programs) == 10
        and set(schedule) == expected_programs
    )


def fitness_chart(history):
    """Build a chart for one trial's fitness history."""
    fitness_df = pd.DataFrame({
        "Generation": range(len(history)),
        "Best Fitness": history
    })

    minimum = max(0, min(history) - 0.5)
    maximum = max(history) + 0.5

    return (
        alt.Chart(fitness_df)
        .mark_line(
            color="#4A9EEB",
            strokeWidth=3,
            point=alt.OverlayMarkDef(
                filled=True,
                size=25
            )
        )
        .encode(
            x=alt.X(
                "Generation:Q",
                title="Generation",
                scale=alt.Scale(
                    domain=[0, len(history) - 1],
                    nice=False
                ),
                axis=alt.Axis(
                    values=[0, 20, 40, 60, 80, 100]
                )
            ),
            y=alt.Y(
                "Best Fitness:Q",
                title="Best fitness score",
                scale=alt.Scale(
                    domain=[minimum, maximum],
                    zero=False,
                    nice=False
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "Generation:Q",
                    title="Generation"
                ),
                alt.Tooltip(
                    "Best Fitness:Q",
                    title="Best fitness",
                    format=".2f"
                )
            ]
        )
        .properties(height=300)
    )


def display_schedule_table(schedule_df):
    """Display all 18 rows in a readable table."""
    st.dataframe(
        schedule_df,
        width="stretch",
        hide_index=True,
        height=680,
        column_config={
            "Time Slot": st.column_config.TextColumn(
                "Time slot"
            ),
            "Programme": st.column_config.TextColumn(
                "Programme"
            ),
            "Rating": st.column_config.NumberColumn(
                "Rating",
                format="%.2f"
            )
        }
    )


def display_validation(result):
    """Show schedule validation results."""
    schedule = result["schedule"]
    programs = result["programs"]

    total_slots = len(schedule)
    unique_programs = len(set(schedule))

    col1, col2 = st.columns(2)

    col1.metric("Time slots", f"{total_slots} / 18")
    col2.metric("Unique programmes", f"{unique_programs} / 10")

    if validate_schedule(schedule, programs):
        st.success(
            "Validation passed: the schedule contains 18 time slots "
            "and includes all 10 programmes."
        )
    else:
        st.error(
            "Validation failed: check the time slots and "
            "programme coverage."
        )


# ==================================================
# HEADER
# ==================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-label">Evolutionary Computing</div>
        <div class="hero-title">TV Scheduling Dashboard</div>
        <div class="hero-description">
            Generate TV schedules with a genetic algorithm,
            explore the results, and compare up to three trials.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("How to use this dashboard"):
    st.markdown(
        """
        1. Choose a **crossover rate** and a **mutation rate**.
        2. Click **Generate TV schedule**.
        3. Review the schedule, fitness chart and validation.
        4. Click **Save current result as a trial**.
        5. Change the rates and repeat to compare up to three trials.

        **Fitness** is the total rating of the programmes assigned
        to the 18 time slots. A higher score is better for this model.

        Saved trials are kept for the current browser session.
        Download the CSV files if you want to keep the results.
        """
    )


# ==================================================
# 1. PARAMETERS
# ==================================================

st.header("1. Set your parameters")
st.caption(
    "Select the rates, then generate a schedule."
)

with st.container(border=True):
    crossover_col, mutation_col = st.columns(2, gap="large")

    with crossover_col:
        st.subheader("Crossover")
        st.caption(
            "Controls how often two parent schedules are combined."
        )

        crossover_rate = st.slider(
            "Crossover rate (CO_R)",
            min_value=0.00,
            max_value=0.95,
            value=0.80,
            step=0.01,
            format="%.2f",
            help=(
                "A higher value gives the algorithm more opportunities "
                "to combine parts of two parent schedules."
            )
        )

    with mutation_col:
        st.subheader("Mutation")
        st.caption(
            "Controls how often an offspring schedule is changed."
        )

        mutation_mode = st.radio(
            "Mutation mode",
            options=[
                "Default (0.20)",
                "Custom (0.01 to 0.05)"
            ],
            horizontal=True
        )

        if mutation_mode == "Default (0.20)":
            mutation_rate = 0.20
            st.caption(
                "The assignment specifies 0.20 as the default."
            )
        else:
            mutation_rate = st.slider(
                "Mutation rate (MUT_R)",
                min_value=0.01,
                max_value=0.05,
                value=0.02,
                step=0.01,
                format="%.2f",
                help=(
                    "Mutation introduces a change into an offspring "
                    "schedule to explore another possible solution."
                )
            )

    st.divider()

    st.markdown("**Fixed experiment settings**")

    setting1, setting2, setting3, setting4 = st.columns(4)

    setting1.metric("Generations", str(GENERATIONS))
    setting2.metric("Population", str(POPULATION_SIZE))
    setting3.metric("Elitism", str(ELITISM_SIZE))
    setting4.metric("Random seed", str(RANDOM_SEED))

    st.write("")

    generate = st.button(
        "Generate TV schedule",
        type="primary",
        width="stretch"
    )


# ==================================================
# RUN THE GENETIC ALGORITHM
# ==================================================

if generate:
    if not CSV_PATH.exists():
        st.error(
            "The modified ratings file was not found. "
            "Check that program_ratings_modified.csv is in "
            "the same GitHub folder as app.py."
        )
    else:
        try:
            with st.spinner("Generating your schedule..."):
                schedule, history, ratings = genetic_algorithm(
                    file_path=str(CSV_PATH),
                    generations=GENERATIONS,
                    population_size=POPULATION_SIZE,
                    crossover_rate=crossover_rate,
                    mutation_rate=mutation_rate,
                    elitism_size=ELITISM_SIZE,
                    seed=RANDOM_SEED
                )

                schedule_df = create_schedule_dataframe(
                    schedule,
                    ratings
                )

                st.session_state.current_result = {
                    "schedule": schedule,
                    "schedule_df": schedule_df,
                    "history": history,
                    "programs": list(ratings.keys()),
                    "crossover_rate": crossover_rate,
                    "mutation_rate": mutation_rate
                }

            st.success("Schedule generated successfully.")

        except Exception as error:
            st.error(f"Unable to generate the schedule: {error}")


# ==================================================
# 2. CURRENT RESULT
# ==================================================

st.write("")
st.header("2. Review your current result")

result = st.session_state.current_result

if result is None:
    st.info(
        "Choose your parameters and generate a schedule "
        "to see the results here."
    )

else:
    initial_fitness = result["history"][0]
    final_fitness = result["history"][-1]
    improvement = final_fitness - initial_fitness
    average_rating = final_fitness / len(result["schedule"])

    st.caption(
        f"Current result: CO_R = {result['crossover_rate']:.2f} "
        f"| MUT_R = {result['mutation_rate']:.2f}"
    )

    if (
        crossover_rate != result["crossover_rate"]
        or mutation_rate != result["mutation_rate"]
    ):
        st.info(
            "The selected parameters have changed. The result below "
            "still belongs to the previous settings. Generate a new "
            "schedule to use the selected rates."
        )

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Initial best fitness",
        f"{initial_fitness:.2f}"
    )

    metric2.metric(
        "Final best fitness",
        f"{final_fitness:.2f}"
    )

    metric3.metric(
        "Fitness improvement",
        f"{improvement:+.2f}"
    )

    metric4.metric(
        "Average rating per slot",
        f"{average_rating:.3f}"
    )

    st.write("")

    # Save the current result as a trial.
    save_col, count_col = st.columns([2, 1])

    with save_col:
        save_trial = st.button(
            "Save current result as a trial",
            disabled=(
                len(st.session_state.saved_trials) >= MAX_TRIALS
            ),
            width="stretch"
        )

    with count_col:
        st.caption(
            f"Saved trials: "
            f"{len(st.session_state.saved_trials)} / {MAX_TRIALS}"
        )

    if save_trial:
        st.session_state.saved_trials.append({
            "schedule": list(result["schedule"]),
            "schedule_df": result["schedule_df"].copy(),
            "history": list(result["history"]),
            "programs": list(result["programs"]),
            "crossover_rate": result["crossover_rate"],
            "mutation_rate": result["mutation_rate"]
        })

        st.rerun()

    if len(st.session_state.saved_trials) >= MAX_TRIALS:
        st.caption(
            "You have saved three trials. Clear the saved trials "
            "below to start a new comparison."
        )

    st.write("")
    st.subheader("Optimized TV schedule")
    st.caption(
        "Each rating is the value assigned to the programme "
        "in its selected time slot."
    )

    display_schedule_table(result["schedule_df"])

    st.download_button(
        "Download current schedule as CSV",
        data=result["schedule_df"].to_csv(
            index=False
        ).encode("utf-8"),
        file_name="current_tv_schedule.csv",
        mime="text/csv"
    )

    st.write("")
    st.subheader("Fitness progress")
    st.caption(
        "Best fitness recorded from the initial population "
        "through generation 100."
    )

    st.altair_chart(
        fitness_chart(result["history"]),
        width="stretch"
    )

    st.write("")
    st.subheader("Schedule validation")
    display_validation(result)


# ==================================================
# 3. COMPARE SAVED TRIALS
# ==================================================

st.write("")
st.header("3. Compare saved trials")

trials = st.session_state.saved_trials

st.caption(
    "Save up to three results to compare parameter combinations. "
    "Trials remain available during your current browser session."
)

if not trials:
    st.info(
        "No trials saved yet. Generate a schedule and click "
        "Save current result as a trial."
    )

else:
    summary_rows = []

    for index, trial in enumerate(trials, start=1):
        initial = trial["history"][0]
        final = trial["history"][-1]

        summary_rows.append({
            "Trial": f"Trial {index}",
            "CO_R": trial["crossover_rate"],
            "MUT_R": trial["mutation_rate"],
            "Initial Fitness": initial,
            "Final Fitness": final,
            "Improvement": final - initial,
            "Average Rating": final / len(trial["schedule"]),
            "Validation": (
                "Passed"
                if validate_schedule(
                    trial["schedule"],
                    trial["programs"]
                )
                else "Failed"
            )
        })

    summary_df = pd.DataFrame(summary_rows)

    st.subheader("Trial summary")

    st.dataframe(
        summary_df,
        width="stretch",
        hide_index=True,
        column_config={
            "CO_R": st.column_config.NumberColumn(
                "CO_R",
                format="%.2f"
            ),
            "MUT_R": st.column_config.NumberColumn(
                "MUT_R",
                format="%.2f"
            ),
            "Initial Fitness": st.column_config.NumberColumn(
                "Initial fitness",
                format="%.2f"
            ),
            "Final Fitness": st.column_config.NumberColumn(
                "Final fitness",
                format="%.2f"
            ),
            "Improvement": st.column_config.NumberColumn(
                "Improvement",
                format="%.2f"
            ),
            "Average Rating": st.column_config.NumberColumn(
                "Average rating",
                format="%.3f"
            )
        }
    )

    best_fitness = summary_df["Final Fitness"].max()

    best_trials = summary_df.loc[
        summary_df["Final Fitness"].round(8)
        == round(best_fitness, 8),
        "Trial"
    ].tolist()

    if len(best_trials) == 1:
        st.success(
            f"Highest saved fitness: {best_trials[0]} "
            f"with {best_fitness:.2f}."
        )
    else:
        st.success(
            f"Highest saved fitness: {best_fitness:.2f}. "
            f"Tied trials: {', '.join(best_trials)}."
        )

    st.download_button(
        "Download trial comparison as CSV",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name="trial_comparison.csv",
        mime="text/csv"
    )

    st.write("")
    st.subheader("Compare final fitness")
    st.caption(
        "Higher fitness means a higher total rating "
        "under the current scheduling model."
    )

    comparison_chart = (
        alt.Chart(summary_df)
        .mark_bar(
            color="#4A9EEB",
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        )
        .encode(
            x=alt.X(
                "Trial:N",
                title="Trial",
                sort=None
            ),
            y=alt.Y(
                "Final Fitness:Q",
                title="Final fitness",
                scale=alt.Scale(zero=True)
            ),
            tooltip=[
                alt.Tooltip("Trial:N"),
                alt.Tooltip("CO_R:Q", format=".2f"),
                alt.Tooltip("MUT_R:Q", format=".2f"),
                alt.Tooltip(
                    "Final Fitness:Q",
                    title="Final fitness",
                    format=".2f"
                )
            ]
        )
        .properties(height=280)
    )

    st.altair_chart(
        comparison_chart,
        width="stretch"
    )

    st.write("")
    st.subheader("Compare fitness progress")

    history_rows = []

    for index, trial in enumerate(trials, start=1):
        for generation, fitness in enumerate(trial["history"]):
            history_rows.append({
                "Trial": f"Trial {index}",
                "Generation": generation,
                "Best Fitness": fitness
            })

    history_df = pd.DataFrame(history_rows)

    progress_chart = (
        alt.Chart(history_df)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X(
                "Generation:Q",
                title="Generation"
            ),
            y=alt.Y(
                "Best Fitness:Q",
                title="Best fitness",
                scale=alt.Scale(zero=False)
            ),
            color=alt.Color(
                "Trial:N",
                title="Trial"
            ),
            tooltip=[
                alt.Tooltip("Trial:N"),
                alt.Tooltip("Generation:Q"),
                alt.Tooltip(
                    "Best Fitness:Q",
                    title="Best fitness",
                    format=".2f"
                )
            ]
        )
        .properties(height=300)
    )

    st.altair_chart(
        progress_chart,
        width="stretch"
    )

    st.write("")
    st.subheader("View a saved schedule")

    selected_label = st.selectbox(
        "Choose a trial",
        options=[
            f"Trial {index}"
            for index in range(1, len(trials) + 1)
        ]
    )

    selected_index = int(selected_label.split()[-1]) - 1
    selected_trial = trials[selected_index]

    st.caption(
        f"{selected_label}: "
        f"CO_R = {selected_trial['crossover_rate']:.2f} "
        f"| MUT_R = {selected_trial['mutation_rate']:.2f}"
    )

    display_schedule_table(selected_trial["schedule_df"])

    st.download_button(
        f"Download {selected_label} schedule as CSV",
        data=selected_trial["schedule_df"].to_csv(
            index=False
        ).encode("utf-8"),
        file_name=f"trial_{selected_index + 1}_schedule.csv",
        mime="text/csv"
    )

    st.write("")
    st.subheader("Start a new comparison")

    if st.button("Clear all saved trials"):
        st.session_state.saved_trials = []
        st.rerun()
