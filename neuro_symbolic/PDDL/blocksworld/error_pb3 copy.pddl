(define (problem blocksworld-problem)
  (:domain blocksworld)
  (:objects a b c - block)
  (:init (handempty) (on a b) (on b c) (ontable c)
         (clear a) (a on b))
  (:goal (and (on-table a) (on-table b) (on-table c)
              (clear a) (clear b) (clear c)))
)
;ontable vs on-table, a on b