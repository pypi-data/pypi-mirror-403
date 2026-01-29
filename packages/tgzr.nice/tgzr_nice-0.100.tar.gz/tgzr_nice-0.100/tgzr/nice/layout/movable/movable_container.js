export default {
    template: `
    <div 
      ref="container"
      class="movable-container"
      :style="containerStyle"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
    >
      <slot></slot>
    </div>
  `,
    props: {
        minWidth: Number,
        minHeight: Number
    },
    data() {
        return {
            containerWidth: this.minWidth,
            containerHeight: this.minHeight,
            draggingMovable: null,
            dragOffsetX: 0,
            dragOffsetY: 0
        };
    },
    computed: {
        containerStyle() {
            return {
                position: 'relative',
                width: this.containerWidth + 'px',
                height: this.containerHeight + 'px',
                // background: '#f5f5f5',
                // border: '2px dashed #ccc',
                // borderRadius: '12px',
                overflow: 'visible',
                transition: 'width 0.2s, height 0.2s'
            };
        }
    },
    provide() {
        return {
            containerRegisterDrag: this.onDragStart
        };
    },
    methods: {
        onMouseMove(event) {
            if (!this.draggingMovable) return;

            const rect = this.$refs.container.getBoundingClientRect();
            const x = event.clientX - rect.left - this.dragOffsetX;
            const y = event.clientY - rect.top - this.dragOffsetY;

            // Update position
            this.draggingMovable.updatePosition(
                // Math.max(0, x),
                // Math.max(0, y)
                x, y
            );

            // // Update container size by querying all movable items
            // this.updateContainerSize();
        },
        onMouseUp() {
            if (this.draggingMovable) {
                this.draggingMovable.setDragging(false);
                this.draggingMovable = null;
            }
            // Update container size by querying all movable items
            this.updateContainerSize();
        },
        updateContainerSize() {
            let maxX = this.minWidth;
            let maxY = this.minHeight;

            let minX = 1000;
            let minY = 1000;

            // Query all movable wrappers directly from the DOM
            const wrappers = this.$el.querySelectorAll('.movable-wrapper');

            wrappers.forEach(wrapper => {
                const rect = wrapper.getBoundingClientRect();
                const containerRect = this.$refs.container.getBoundingClientRect();

                // Calculate position relative to container
                const relativeRight = rect.right - containerRect.left;
                const relativeBottom = rect.bottom - containerRect.top;
                const relativeLeft = rect.left - containerRect.left;
                const relativeTop = rect.top - containerRect.top;

                // maxX = Math.max(maxX, relativeRight + 20);
                // maxY = Math.max(maxY, relativeBottom + 20);
                maxX = Math.max(maxX, relativeRight);
                maxY = Math.max(maxY, relativeBottom);
                minX = Math.min(minX, relativeLeft);
                minY = Math.min(minY, relativeTop);
            });

            this.containerWidth = maxX;// - minX;
            this.containerHeight = maxY;// - minY;
            // this.currentX = minX;
            // this.currentY = minY;
        },
        onDragStart(payload) {
            this.draggingMovable = payload.movable;
            this.dragOffsetX = payload.offsetX;
            this.dragOffsetY = payload.offsetY;
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.updateContainerSize();
        });
    }
};