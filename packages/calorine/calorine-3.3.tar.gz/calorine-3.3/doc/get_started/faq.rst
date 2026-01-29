.. _faq:

FAQ
===

Below you can find answers to some frequently asked questions.  
You may also want to browse previously reported questions and discussions in the
`calorine issue tracker <https://gitlab.com/materials-modeling/calorine/-/issues>`_.

Strange Energies and Forces from CPUNEP
---------------------------------------

Occasionally, the :class:`~calorine.calculators.CPUNEP` calculator may behave unexpectedly
and produce incorrect energies or forces when ``matplotlib`` has been imported in the same
Python script.

**Workarounds:**

- Change the ``matplotlib`` backend to avoid the conflict.  
- Avoid importing ``matplotlib`` in scripts where :class:`~calorine.calculators.CPUNEP` is used.

For further details and discussion, see the
`related issue <https://gitlab.com/materials-modeling/calorine/-/issues/55>`_ in the issue tracker.
