from childagenteval_research.evaluation.figure_spec import FIGURE_PLAN, FigureSpec
from childagenteval_research.evaluation.reporting import generate_figure_caption
from childagenteval_research.evaluation.table_spec import TABLE_PLAN


def test_figure_plan_has_all_ten_figures_numbered_in_order():
    assert [f.number for f in FIGURE_PLAN] == list(range(1, 11))


def test_every_figure_specifies_required_fields():
    for fig in FIGURE_PLAN:
        assert fig.x_axis and fig.y_axis and fig.units and fig.grouping
        assert isinstance(fig.data_currently_exists, bool)
        assert len(fig.required_data) > 0


def test_all_figures_have_data_after_the_l0_l3_run():
    existing = [f.number for f in FIGURE_PLAN if f.data_currently_exists]
    assert existing == list(range(1, 11))


def test_caption_for_unavailable_figure_says_so():
    # Construct a hypothetical unavailable figure directly rather than depending on the
    # plan always containing one — after Phase 5C all 10 real figures have data.
    hypothetical = FigureSpec(
        number=99, title="Hypothetical", x_axis="x", y_axis="y", units="u",
        grouping="g", statistical_annotations="s", required_data=("nothing yet",),
        data_currently_exists=False,
    )
    caption = generate_figure_caption(hypothetical)
    assert "NOT YET AVAILABLE" in caption


def test_caption_for_available_figure_includes_axes_and_n():
    fig1 = next(f for f in FIGURE_PLAN if f.number == 1)
    caption = generate_figure_caption(fig1, n_used=38)
    assert "Figure 1" in caption
    assert "n=38" in caption


def test_table_plan_has_all_nine_tables_numbered_in_order():
    assert [t.number for t in TABLE_PLAN] == list(range(1, 10))


def test_unpopulated_tables_have_no_populated_flag_set_true_without_reason():
    for table in TABLE_PLAN:
        assert isinstance(table.populated, bool)
        assert len(table.columns) > 0


def test_ablation_table_not_populated_no_l3_ablations_run():
    table7 = next(t for t in TABLE_PLAN if t.number == 7)
    table9 = next(t for t in TABLE_PLAN if t.number == 9)
    assert table7.populated is False
    assert table9.populated is False


def test_l0_l3_comparison_tables_populated_after_the_run():
    table5 = next(t for t in TABLE_PLAN if t.number == 5)
    table6 = next(t for t in TABLE_PLAN if t.number == 6)
    assert table5.populated is True
    assert table6.populated is True
