export default {
    template: `
    <div 
      class="movable-wrapper"
      :style="wrapperStyle"
      @mousedown="onMouseDown"
    >
      <slot></slot>
    </div>
  `,
    props: {
        x: Number,
        y: Number
    },
    inject: ['containerRegisterDrag'],
    data() {
        return {
            currentX: this.x,
            currentY: this.y,
            isDragging: false
        };
    },
    computed: {
        wrapperStyle() {
            return {
                position: 'absolute',
                left: this.currentX + 'px',
                top: this.currentY + 'px',
                cursor: 'move',
                userSelect: 'none',
                zIndex: this.isDragging ? 1000 : 'auto'
            };
        }
    },
    methods: {
        onMouseDown(event) {
            this.isDragging = true;
            const offsetX = event.offsetX;
            const offsetY = event.offsetY;

            // Call parent container's drag handler via provide/inject
            this.containerRegisterDrag({
                movable: this,
                offsetX,
                offsetY
            });

            event.preventDefault();
            event.stopPropagation();
        },
        updatePosition(x, y) {
            this.currentX = x;
            this.currentY = y;
        },
        setDragging(dragging) {
            this.isDragging = dragging;
        },
        getBounds() {
            const el = this.$el;
            return {
                x: this.currentX,
                y: this.currentY,
                width: el.offsetWidth,
                height: el.offsetHeight,
                right: this.currentX + el.offsetWidth,
                bottom: this.currentY + el.offsetHeight
            };
        },
        getSize() {
            const el = this.$el;
            return [
                this.offsetWidth,
                this.offsetHeight
            ];
        }
    }
};