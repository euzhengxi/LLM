(define (problem blocksworld-problem)
  (:domain blocksworld)
  (:objects a b c - block)
  (:init (handempty) (on a b) (on b c) (ontable c)
         (clear a))
  (:goal (and (ontable a) (ontable b) (ontable c)
              (clear a) (clear b) (clear c) (on a b)))
)
;conflict on a b vs on b a